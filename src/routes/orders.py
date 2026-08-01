import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status
from loguru import logger
from pydantic import BaseModel

from src.config import settings
from src.dependencies import get_invoice_upload_repo
from src.models.invoice import InvoiceUploadStatus
from src.tasks.invoice_tasks import process_invoice_upload

router = APIRouter(prefix="/orders", tags=["orders"])

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
PDF_MAGIC = b"%PDF-"


class InvoiceUploadAccepted(BaseModel):
    """All the uploader gets back. Processing happens in a worker."""

    upload_id: uuid.UUID
    status: InvoiceUploadStatus
    duplicate: bool


class InvoiceUploadStatusResponse(BaseModel):
    upload_id: uuid.UUID
    filename: str
    status: InvoiceUploadStatus
    failure_reason: str | None = None
    transaction_id: str | None = None
    order_id: uuid.UUID | None = None
    attempts: int


@router.post(
    "/invoices",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=InvoiceUploadAccepted,
)
async def upload_invoice(file: UploadFile) -> InvoiceUploadAccepted:
    """Accept an invoice PDF for background processing.

    The response confirms acceptance only. Whether the invoice parsed, matched
    a transaction, or turned out to hold nothing useful is discoverable through
    ``GET /orders/invoices/{upload_id}``.
    """
    content = await file.read()
    await file.close()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload"
        )

    if len(content) > settings.invoice_max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Invoice exceeds {settings.invoice_max_upload_bytes} bytes"
            ),
        )

    # Trust the magic bytes over the declared content type, but require one of
    # them to say PDF -- docling would otherwise spend real time on junk.
    if file.content_type not in PDF_CONTENT_TYPES and not content.startswith(
        PDF_MAGIC
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF invoices are accepted",
        )

    repo = get_invoice_upload_repo()
    upload, created = repo.create(
        filename=file.filename or "invoice.pdf",
        content=content,
        content_type=file.content_type or "application/pdf",
    )

    if created:
        process_invoice_upload.delay(str(upload.id))
    else:
        # Same bytes as an earlier upload: hand back the original handle rather
        # than processing it a second time.
        logger.info(f"Invoice {upload.id} already accepted; not reprocessing")

    return InvoiceUploadAccepted(
        upload_id=upload.id, status=upload.status, duplicate=not created
    )


@router.get(
    "/invoices/{upload_id}",
    response_model=InvoiceUploadStatusResponse,
)
async def get_invoice_upload(upload_id: uuid.UUID) -> InvoiceUploadStatusResponse:
    """Report what became of an uploaded invoice."""
    upload = get_invoice_upload_repo().get(upload_id)
    if upload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown upload"
        )

    return InvoiceUploadStatusResponse(
        upload_id=upload.id,
        filename=upload.filename,
        status=upload.status,
        failure_reason=upload.failure_reason,
        transaction_id=upload.transaction_id,
        order_id=upload.order_id,
        attempts=upload.attempts,
    )
