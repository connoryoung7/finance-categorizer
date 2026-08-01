from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from src.models.budget import Transaction
from src.models.order import ExtractedOrder


class MatchReason(str, Enum):
    """Why a matching attempt did or did not produce a transaction."""

    MATCHED = "matched"
    NO_CANDIDATES = "no_candidates"
    AMBIGUOUS = "ambiguous"


class TransactionMatch(BaseModel):
    """The outcome of matching an extracted order to a transaction.

    ``transaction`` is set only when exactly one candidate survived. Ambiguity
    is reported, never resolved by guessing -- a wrong attachment is silent and
    very hard to detect after the fact.
    """

    transaction: Transaction | None = None
    reason: MatchReason
    candidate_count: int = 0

    @property
    def is_matched(self) -> bool:
        return self.transaction is not None


class InvoiceUploadStatus(str, Enum):
    """Lifecycle of an uploaded invoice.

    ``accepted`` and ``parsing`` are transient. ``matched`` and ``failed`` are
    terminal. ``unmatched`` is retried whenever new transactions are synced --
    an invoice uploaded before its charge posts resolves on its own.
    """

    ACCEPTED = "accepted"
    PARSING = "parsing"
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    FAILED = "failed"


class InvoiceUpload(BaseModel):
    """An uploaded invoice and the outcome of processing it.

    The uploaded bytes are deliberately not carried here -- they are fetched
    separately via the repository so that status reads stay cheap.
    """

    id: UUID
    filename: str
    content_hash: str
    content_type: str
    status: InvoiceUploadStatus
    failure_reason: str | None = None
    # Persisted once extraction succeeds, so that re-matching an unmatched
    # upload never re-runs the (paid, non-deterministic) LLM call.
    extracted_order: ExtractedOrder | None = None
    transaction_id: str | None = None
    order_id: UUID | None = None
    attempts: int = 0
