from datetime import UTC, datetime
from decimal import Decimal
import uuid

from sqlalchemy import Engine, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.interfaces.order_repo import OrderRepoInterface
from src.models.order import Order
from src.models.orm import OrderItemRecord, OrderRecord

# All money is stored as integer milliunits, matching TransactionRecord.amount.
MILLIUNITS = 1000


def _to_milliunits(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return int((value * MILLIUNITS).to_integral_value())


class OrderPostgresRepo(OrderRepoInterface):
    def __init__(self, db: Engine):
        self.db = db

    def upsert_order(self, order: Order) -> uuid.UUID:
        with Session(self.db) as session:
            stmt = insert(OrderRecord).values(
                transaction_id=order.transaction_id,
                order_number=order.order_number,
                overall_cost=_to_milliunits(order.overall_cost),
                total_tax=_to_milliunits(order.total_tax),
                tip=_to_milliunits(order.tip),
                total_amount=_to_milliunits(order.total_amount),
                status=order.status,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["transaction_id", "order_number"],
                set_={
                    "overall_cost": stmt.excluded.overall_cost,
                    "total_tax": stmt.excluded.total_tax,
                    "tip": stmt.excluded.tip,
                    "total_amount": stmt.excluded.total_amount,
                    "status": stmt.excluded.status,
                    "updated_at": datetime.now(UTC),
                },
            ).returning(OrderRecord.id)

            order_id = session.execute(stmt).scalar_one()

            # Line items are delete-and-replace on every ingest.
            session.execute(
                delete(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )

            if order.products:
                session.execute(
                    insert(OrderItemRecord),
                    [
                        {
                            "id": product.id,
                            "order_id": order_id,
                            "name": product.name,
                            "price": _to_milliunits(product.price),
                            "quantity": product.quantity,
                        }
                        for product in order.products
                    ],
                )

            session.commit()
            return order_id
