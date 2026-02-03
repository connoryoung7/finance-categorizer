from pydantic import BaseClass

import datetime

class AmazonOrder(BaseClass):
    id: str
    date: datetime.date
    total_cost: int 

class AmazonOrderItem(BaseClass):
    order_id: str
    product_name: str
    total_cost: int
    num_of_items: int
    unit_price: int
