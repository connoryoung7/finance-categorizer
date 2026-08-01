from datetime import UTC, datetime
from decimal import Decimal
import uuid

from sqlalchemy import Engine, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.interfaces.order_repo import OrderRepoInterface
from src.models.order import Order, Product
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
                status=order.status.value,
                reconciled=order.reconciled,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["transaction_id"],
                set_={
                    "order_number": stmt.excluded.order_number,
                    "overall_cost": stmt.excluded.overall_cost,
                    "total_tax": stmt.excluded.total_tax,
                    "tip": stmt.excluded.tip,
                    "total_amount": stmt.excluded.total_amount,
                    "status": stmt.excluded.status,
                    "reconciled": stmt.excluded.reconciled,
                    "updated_at": datetime.now(UTC),
                },
            ).returning(OrderRecord.id)

            order_id = session.execute(stmt).scalar_one()

            # Line items are delete-and-replace, so any category assigned by a
            # later categorization step has to be carried across explicitly.
            preserved = self._existing_categories(session, order_id)

            session.execute(
                delete(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )

            if order.products:
                session.execute(
                    insert(OrderItemRecord),
                    [
                        {
                            "order_id": order_id,
                            "line_number": line_number,
                            "name": product.name,
                            "price": _to_milliunits(product.price),
                            "quantity": product.quantity,
                            "external_id": product.external_id,
                            "category_id": self._category_for(product, preserved),
                        }
                        for line_number, product in enumerate(order.products, start=1)
                    ],
                )

            session.commit()
            return order_id

    def _existing_categories(
        self, session: Session, order_id: uuid.UUID
    ) -> dict[tuple[str, str], str]:
        """Category ids already assigned to this order's line items.

        Keyed both by external id and by name so a re-ingest can re-attach them
        even when the vendor omits one or the other.
        """
        records = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .all()
        )

        preserved: dict[tuple[str, str], str] = {}
        for record in records:
            if not record.category_id:
                continue
            if record.external_id:
                preserved[("external_id", record.external_id)] = record.category_id
            preserved.setdefault(("name", record.name), record.category_id)
        return preserved

    def _category_for(
        self, product: Product, preserved: dict[tuple[str, str], str]
    ) -> str | None:
        if product.category_id:
            return product.category_id
        if product.external_id:
            match = preserved.get(("external_id", product.external_id))
            if match:
                return match
        return preserved.get(("name", product.name))
