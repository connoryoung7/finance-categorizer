from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.config import settings
from src.models.order import Order, Product
from src.models.orm import Base, OrderItemRecord, OrderRecord, TransactionRecord
from src.repos.order_postgres_repo import OrderPostgresRepo

TRANSACTION_ID = "txn-test-1"


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(settings.database_url)
    try:
        with eng.connect():
            pass
    except OperationalError:
        pytest.skip("PostgreSQL is not reachable")
    return eng


@pytest.fixture
def db(engine):
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            TransactionRecord(
                id=TRANSACTION_ID, amount=0, approved=False, deleted=False
            )
        )
        session.commit()
    yield engine
    Base.metadata.drop_all(engine)


def _order(status: str = "pending", products: list[Product] | None = None) -> Order:
    return Order(
        transaction_id=TRANSACTION_ID,
        order_number="112-ABC",
        overall_cost=Decimal("20.00"),
        total_tax=Decimal("1.50"),
        tip=None,
        total_amount=Decimal("21.50"),
        status=status,
        products=products
        if products is not None
        else [Product(id=1, name="Coffee", price=Decimal("10.00"), quantity=2)],
    )


def test_insert_creates_order_and_items(db):
    repo = OrderPostgresRepo(db)
    order_id = repo.upsert_order(_order())

    with Session(db) as session:
        record = session.get(OrderRecord, order_id)
        assert record.overall_cost == 20000
        assert record.total_tax == 1500
        assert record.total_amount == 21500
        assert record.tip is None

        items = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .all()
        )
        assert len(items) == 1
        assert items[0].price == 10000
        assert items[0].quantity == 2


def test_reingest_updates_in_place_and_replaces_items(db):
    repo = OrderPostgresRepo(db)
    first_id = repo.upsert_order(_order(status="pending"))
    second_id = repo.upsert_order(
        _order(
            status="shipped",
            products=[Product(id=2, name="Tea", price=Decimal("5.00"), quantity=1)],
        )
    )

    # Same idempotency key -> same stable UUID, updated in place.
    assert first_id == second_id

    with Session(db) as session:
        record = session.get(OrderRecord, second_id)
        assert record.status == "shipped"

        items = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == second_id)
            )
            .scalars()
            .all()
        )
        assert len(items) == 1
        assert items[0].id == 2
        assert items[0].name == "Tea"


def test_delete_order_cascades_items(db):
    repo = OrderPostgresRepo(db)
    order_id = repo.upsert_order(_order())

    with Session(db) as session:
        session.delete(session.get(OrderRecord, order_id))
        session.commit()

    with Session(db) as session:
        items = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .all()
        )
        assert items == []


def test_tip_persisted_when_present(db):
    repo = OrderPostgresRepo(db)
    order = _order()
    order.tip = Decimal("3.00")
    order_id = repo.upsert_order(order)

    with Session(db) as session:
        record = session.get(OrderRecord, order_id)
        assert record.tip == 3000
