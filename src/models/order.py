from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, PositiveInt


class Product(BaseModel):
    id: int
    name: str
    price: Decimal = Field(..., ge=0)
    quantity: PositiveInt
    # YNAB category id, assigned later by a categorization step (NULL at ingest).
    category_id: str | None = None


class Order(BaseModel):
    id: UUID | None = None
    transaction_id: str
    order_number: str
    overall_cost: Decimal = Field(..., ge=0)
    total_tax: Decimal = Field(..., ge=0)
    tip: Decimal | None = Field(default=None, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    status: str
    products: list[Product]
