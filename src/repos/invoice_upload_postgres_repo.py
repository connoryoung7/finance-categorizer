from datetime import UTC, datetime
import hashlib
import uuid

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from src.interfaces.invoice_upload_repo import InvoiceUploadRepoInterface
from src.models.invoice import InvoiceUpload, InvoiceUploadStatus
from src.models.order import ExtractedOrder
from src.models.orm import InvoiceUploadRecord


def _to_domain(record: InvoiceUploadRecord) -> InvoiceUpload:
    return InvoiceUpload(
        id=record.id,
        filename=record.filename,
        content_hash=record.content_hash,
        content_type=record.content_type,
        status=InvoiceUploadStatus(record.status),
        failure_reason=record.failure_reason,
        extracted_order=(
            ExtractedOrder.model_validate(record.extracted_order)
            if record.extracted_order
            else None
        ),
        transaction_id=record.transaction_id,
        order_id=record.order_id,
        attempts=record.attempts,
    )


class InvoiceUploadPostgresRepo(InvoiceUploadRepoInterface):
    def __init__(self, db: Engine):
        self.db = db

    def create(
        self, filename: str, content: bytes, content_type: str
    ) -> tuple[InvoiceUpload, bool]:
        content_hash = hashlib.sha256(content).hexdigest()

        with Session(self.db) as session:
            existing = session.execute(
                select(InvoiceUploadRecord).where(
                    InvoiceUploadRecord.content_hash == content_hash
                )
            ).scalar_one_or_none()
            if existing:
                return _to_domain(existing), False

            record = InvoiceUploadRecord(
                id=uuid.uuid4(),
                filename=filename,
                content_hash=content_hash,
                content=content,
                content_type=content_type,
                status=InvoiceUploadStatus.ACCEPTED.value,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return _to_domain(record), True

    def get(self, upload_id: uuid.UUID) -> InvoiceUpload | None:
        with Session(self.db) as session:
            record = session.get(InvoiceUploadRecord, upload_id)
            return _to_domain(record) if record else None

    def get_content(self, upload_id: uuid.UUID) -> bytes | None:
        with Session(self.db) as session:
            record = session.get(InvoiceUploadRecord, upload_id)
            return record.content if record else None

    def list_by_status(self, status: InvoiceUploadStatus) -> list[InvoiceUpload]:
        with Session(self.db) as session:
            records = (
                session.execute(
                    select(InvoiceUploadRecord)
                    .where(InvoiceUploadRecord.status == status.value)
                    .order_by(InvoiceUploadRecord.created_at)
                )
                .scalars()
                .all()
            )
            return [_to_domain(record) for record in records]

    def update_status(
        self,
        upload_id: uuid.UUID,
        status: InvoiceUploadStatus,
        failure_reason: str | None = None,
        extracted_order: ExtractedOrder | None = None,
        transaction_id: str | None = None,
        order_id: uuid.UUID | None = None,
        increment_attempts: bool = False,
    ) -> None:
        with Session(self.db) as session:
            record = session.get(InvoiceUploadRecord, upload_id)
            if record is None:
                return

            record.status = status.value
            record.failure_reason = failure_reason
            if extracted_order is not None:
                record.extracted_order = extracted_order.model_dump(mode="json")
            if transaction_id is not None:
                record.transaction_id = transaction_id
            if order_id is not None:
                record.order_id = order_id
            if increment_attempts:
                record.attempts += 1
            record.updated_at = datetime.now(UTC)

            session.commit()
