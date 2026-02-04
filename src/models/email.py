from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class EmailCategory(str, Enum):
    """Categories for classifying emails."""

    RECEIPT = "receipt"
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPPING_NOTIFICATION = "shipping_notification"
    NEWSLETTER = "newsletter"
    PROMOTIONAL = "promotional"
    TRANSACTION_ALERT = "transaction_alert"
    OTHER = "other"


class RawBody(BaseModel):
    text: str | None = None
    html: str | None = None


class Email(BaseModel):
    subject: str
    to: list[EmailStr]
    from_: EmailStr = Field(..., alias="from")
    body: RawBody

    class Config:
        populate_by_name = True

@dataclass
class EmailFilters:
    subject: str | None = None
    """Start date is inclusive and should be in ISO 8601 format."""
    start_date: str | None = None
    """End date is inclusive and should be in ISO 8601 format."""
    end_date: str | None = None
