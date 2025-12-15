from enum import IntEnum
from typing import Optional

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
    payee_id: Optional[StrictStr]
    payee_name: Optional[StrictStr]
    date: Optional[StrictStr]
    amount: int
    memo: Optional[StrictStr]
    category_id: str | None
    category_name: str | None
    approved: bool

class PayeeCategorization(BaseModel):
    id: str
    category_id: str
    payee_id: str
    status: str
