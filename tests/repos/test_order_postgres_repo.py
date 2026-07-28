from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.config import settings
from src.models.order import Order, Product
from src.models.orm import Base, OrderItemRecord, OrderRecord, TransactionRecord
from src.repos.order_postgres_repo import OrderPostgresRepo

TRANSACTION_ID = "txn-test-1"


@pytest.fixture(scope="module")
def engine():
    # Always the dedicated test database -- these tests truncate what they find.
    eng = create_engine(settings.test_database_url)
    try:
        with eng.connect():
            pass
    except OperationalError:
        pytest.skip("Test PostgreSQL database is not reachable")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        session.execute(
            text(
                "TRUNCATE order_items, orders, transactions "
                "RESTART IDENTITY CASCADE"
            )
        )
        session.add(
            TransactionRecord(
                id=TRANSACTION_ID, amount=0, approved=False, deleted=False
            )
        )
        session.commit()
    return engine


def _order(
    status: str = "pending",
    products: list[Product] | None = None,
    order_number: str = "112-ABC",
) -> Order:
    return Order(
        transaction_id=TRANSACTION_ID,
        order_number=order_number,
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
        assert isinstance(items[0].id, UUID)
        assert items[0].line_number == 1
        assert items[0].price == 10000
        assert items[0].quantity == 2
        assert items[0].category_id is None


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
        assert isinstance(items[0].id, UUID)
        assert items[0].line_number == 1
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


def test_line_number_is_unique_per_order(db):
    repo = OrderPostgresRepo(db)
    shared = [
        Product(id=999, name="Coffee", price=Decimal("10.00"), quantity=2),
        Product(id=999, name="Tea", price=Decimal("5.00"), quantity=1),
    ]

    first_id = repo.upsert_order(_order(order_number="112-ABC", products=shared))
    second_id = repo.upsert_order(_order(order_number="113-XYZ", products=shared))

    assert first_id != second_id

    with Session(db) as session:
        items = (
            session.execute(
                select(OrderItemRecord).where(
                    OrderItemRecord.order_id.in_([first_id, second_id])
                )
            )
            .scalars()
            .all()
        )
        assert len(items) == 4
        assert {item.order_id for item in items} == {first_id, second_id}
        assert len({item.id for item in items}) == 4
        assert {
            (item.order_id, item.line_number) for item in items
        } == {
            (first_id, 1),
            (first_id, 2),
            (second_id, 1),
            (second_id, 2),
        }


def test_category_id_round_trips_when_set(db):
    repo = OrderPostgresRepo(db)
    order = _order(
        products=[
            Product(
                id=1,
                name="Coffee",
                price=Decimal("10.00"),
                quantity=2,
                category_id="cat-abc",
            )
        ]
    )
    order_id = repo.upsert_order(order)

    with Session(db) as session:
        item = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .one()
        )
        assert item.category_id == "cat-abc"


def test_tip_persisted_when_present(db):
    repo = OrderPostgresRepo(db)
    order = _order()
    order.tip = Decimal("3.00")
    order_id = repo.upsert_order(order)

    with Session(db) as session:
        record = session.get(OrderRecord, order_id)
        assert record.tip == 3000
