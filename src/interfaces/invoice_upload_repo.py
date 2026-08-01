from abc import ABC, abstractmethod
import uuid

from src.models.invoice import InvoiceUpload, InvoiceUploadStatus
from src.models.order import ExtractedOrder


class InvoiceUploadRepoInterface(ABC):
    """Persistence for uploaded invoices and the outcome of processing them."""

    @abstractmethod
    def create(
        self, filename: str, content: bytes, content_type: str
    ) -> tuple[InvoiceUpload, bool]:
        """Record an accepted upload, or return the existing one.

        Uploads are deduplicated on the SHA-256 of their content, because the
        transaction an invoice belongs to is unknown at accept time.

        Args:
            filename: The client-supplied filename.
            content: The raw uploaded bytes.
            content_type: The client-supplied MIME type.

        Returns:
            The upload and whether it was newly created. ``False`` means an
            identical file was already accepted and must not be reprocessed.
        """
        pass

    @abstractmethod
    def get(self, upload_id: uuid.UUID) -> InvoiceUpload | None:
        """Fetch an upload's metadata and outcome, without its bytes."""
        pass

    @abstractmethod
    def get_content(self, upload_id: uuid.UUID) -> bytes | None:
        """Fetch an upload's raw bytes, or None if it does not exist."""
        pass

    @abstractmethod
    def list_by_status(self, status: InvoiceUploadStatus) -> list[InvoiceUpload]:
        """All uploads currently in the given status."""
        pass

    @abstractmethod
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
        """Record the result of a processing step.

        Only the arguments that are supplied are written, so a later step
        cannot clobber what an earlier one recorded.
        """
        pass
