import datetime

from pydantic import BaseModel


class AmazonOrder(BaseModel):
    id: str
    date: datetime.date
    total_cost: int


class AmazonOrderItem(BaseModel):
    order_id: str
    product_name: str
    total_cost: int
    num_of_items: int
    unit_price: int
