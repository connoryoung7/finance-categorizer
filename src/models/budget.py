from datetime import datetime
from enum import Enum, IntEnum

from pydantic import BaseModel, StrictStr


class ConfidenceLevel(IntEnum):
    MediumConfidence = 90
    HighConfidence = 95

class CategoryGroup(BaseModel):
    id: str
    name: str

class Category(BaseModel):
    id: str
    name: str
    category_group: CategoryGroup

class Transaction(BaseModel):
    id: str
    payee_id: StrictStr | None
    payee_name: StrictStr | None
    date: StrictStr | None
    amount: int
    memo: StrictStr | None
    category_id: str | None
    category_name: str | None
    approved: bool
    account_id: str | None = None
    account_name: str | None = None
    deleted: bool = False

class Payee(BaseModel):
    id: str
    name: str

class PayeeCategorization(BaseModel):
    id: str
    category_id: str
    payee_id: str
    status: str

class TransactionEmail(BaseModel):
    id: str
    transaction_id: str
    email_id: str
    date: datetime
    markdown_body: StrictStr | None

class PayeeCategorizationStatus(str, Enum):
    """
    Enum representing the status of a payee categorization.

    Attributes:
        Approved (str): Indicates that the categorization has been
            approved by a human.
        Suggested (str): Indicates that the categorization is suggested
            by the AI, but is waiting for approval by a human.
        Rejected (str): Indicates that the categorization has been
            rejected by a human, and shouldn't be used as a category
            for a given payee.
        Pending (str): Indicates that the system has tried to generate
            a suggested categorization, but it doesn't have a high
            enough confidence level to suggest it to a human for
            approval.
    """
    Approved = "APPROVED"
    Suggested = "SUGGESTED"
    Rejected = "REJECTED"
    Pending = "PENDING"
