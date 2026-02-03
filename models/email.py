from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

class RawBody(BaseModel):
    text: Optional[str] = None
    html: Optional[str] = None


class Email(BaseModel):
    subject: str
    to: List[EmailStr]
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
