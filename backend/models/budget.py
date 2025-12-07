from enum import IntEnum

from pydantic import BaseModel

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
    payee_id: str
    payee_name: str
    date: str
    amount: int
    memo: str
    category_id: str | None
    category_name: str | None
    approved: bool
