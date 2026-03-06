from pydantic import BaseModel, Decimal, Field, PositiveInt


class Product(BaseModel):
    id: str
    name: str
    price: Decimal = Field(..., ge=0.00)
    quantity: PositiveInt


class Order(BaseModel):
    id: str
    total_amount: Decimal = Field(..., ge=0.00)
    products: list[Product]
    status: str
