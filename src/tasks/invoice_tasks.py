import uuid

from loguru import logger

from src.models.invoice import InvoiceUploadStatus
from src.tasks import app


def _services():
    # Imported lazily so that importing this module (which Celery does at
    # worker start) does not build the docling models or an LLM client.
    from src.dependencies import (
        get_document_parser,
        get_invoice_extractor,
        get_invoice_upload_repo,
        get_order_ingestion_service,
        get_order_matching_service,
    )

    return (
        get_invoice_upload_repo(),
        get_document_parser(),
        get_invoice_extractor(),
        get_order_matching_service(),
        get_order_ingestion_service(),
    )


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_invoice_upload(self, upload_id: str) -> dict:
    """Parse an uploaded invoice, match it to a transaction, and write the order.

    Nothing is returned to the uploader, so every outcome is recorded on the
    upload row instead. A document that cannot be parsed or extracted is a
    terminal ``failed`` -- it is never retried, because retrying a bad PDF just
    spends money against the LLM provider. Only infrastructure failures retry.
    """
    upload_uuid = uuid.UUID(upload_id)
    repo, parser, extractor, matcher, ingester = _services()

    upload = repo.get(upload_uuid)
    if upload is None:
        logger.error(f"Invoice upload {upload_id} no longer exists")
        return {"status": "missing", "upload_id": upload_id}

    repo.update_status(
        upload_uuid, InvoiceUploadStatus.PARSING, increment_attempts=True
    )

    try:
        content = repo.get_content(upload_uuid)
        markdown = parser.parse(content or b"", filename=upload.filename)

        if not markdown:
            return _fail(
                repo, upload_uuid, "Document could not be read as a PDF"
            )

        extracted = extractor.extract(markdown)
        if extracted is None:
            return _fail(
                repo, upload_uuid, "No order could be extracted from the document"
            )
    except Exception as exc:
        # Provider outages, database blips -- worth another attempt.
        logger.error(f"Invoice upload {upload_id} failed with a retryable error: {exc}")
        raise self.retry(exc=exc) from exc

    return _match_and_write(repo, matcher, ingester, upload_uuid, extracted)


@app.task
def retry_unmatched_invoices() -> dict:
    """Re-attempt matching for invoices whose charge had not posted yet.

    Runs after each YNAB sync. Extraction is never repeated -- the stored
    ``extracted_order`` is reused.
    """
    repo, _, _, matcher, ingester = _services()

    unmatched = repo.list_by_status(InvoiceUploadStatus.UNMATCHED)
    resolved = 0

    for upload in unmatched:
        if upload.extracted_order is None:
            continue
        result = _match_and_write(
            repo, matcher, ingester, upload.id, upload.extracted_order
        )
        if result["status"] == InvoiceUploadStatus.MATCHED.value:
            resolved += 1

    return {"considered": len(unmatched), "resolved": resolved}


def _match_and_write(repo, matcher, ingester, upload_id, extracted) -> dict:
    """Match an extracted order to a transaction and persist it, or park it."""
    match = matcher.match(extracted)

    if not match.is_matched:
        repo.update_status(
            upload_id,
            InvoiceUploadStatus.UNMATCHED,
            failure_reason=(
                f"{match.reason.value} "
                f"({match.candidate_count} candidate transactions)"
            ),
            extracted_order=extracted,
        )
        return {
            "status": InvoiceUploadStatus.UNMATCHED.value,
            "upload_id": str(upload_id),
            "reason": match.reason.value,
        }

    order_id = ingester.ingest(extracted, match.transaction)
    repo.update_status(
        upload_id,
        InvoiceUploadStatus.MATCHED,
        extracted_order=extracted,
        transaction_id=match.transaction.id,
        order_id=order_id,
    )
    return {
        "status": InvoiceUploadStatus.MATCHED.value,
        "upload_id": str(upload_id),
        "order_id": str(order_id),
    }


def _fail(repo, upload_id: uuid.UUID, reason: str) -> dict:
    logger.warning(f"Invoice upload {upload_id} failed terminally: {reason}")
    repo.update_status(
        upload_id, InvoiceUploadStatus.FAILED, failure_reason=reason
    )
    return {
        "status": InvoiceUploadStatus.FAILED.value,
        "upload_id": str(upload_id),
        "reason": reason,
    }
