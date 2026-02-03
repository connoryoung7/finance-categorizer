import csv
from io import BytesIO
from typing import List

from models.amazon import AmazonOrder, AmazonOrderItem

AMAZON_ONLINE_ORDER_WEBSITE = ""

class AmazonService:
    def __init__(self):
        pass

    @staticmethod
    def parse_amazon_order_file(file_bytes: bytes) -> List[AmazonOrder]:
        byte_stream = BytesIO(file_bytes)
        reader = csv.reader(byte_stream.read().decode('utf-8').splitlines())

        orders: dict[str, AmazonOrder] = {}
        order_items: dict[str, List[AmazonOrderItem]] = {}
        for row in reader:
            if row["Website"] == AMAZON_ONLINE_ORDER_WEBSITE:
                order_id = row["Order ID"]

                if order_id not in orders:
                    orders[order_id] = AmazonOrder(
                        id=order_id,
                        date="",
                        total_cost=0
                    )
                    order_items[order_id] = []

                product_cost = row["Total Owed"]
                product_name = row["Product Name"]
                product_quantity = row["Quantity"]
                product_unit_price = row["Unit Price"]

                order_items[order_id].extend(AmazonOrderItem(
                    order_id=order_id,
                    product_name=product_name,
                    total_cost=product_cost,
                    num_of_items=product_quantity,
                    unit_price=product_unit_price
                ))
