from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.config import settings
from src.models.order import Order, OrderStatus, Product
from src.models.orm import Base, OrderItemRecord, OrderRecord, TransactionRecord
from src.repos.order_postgres_repo import OrderPostgresRepo

TRANSACTION_ID = "txn-test-1"
OTHER_TRANSACTION_ID = "txn-test-2"


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
                "TRUNCATE invoice_uploads, order_items, orders, transactions "
                "RESTART IDENTITY CASCADE"
            )
        )
        session.add_all(
            [
                TransactionRecord(
                    id=TRANSACTION_ID, amount=0, approved=False, deleted=False
                ),
                TransactionRecord(
                    id=OTHER_TRANSACTION_ID,
                    amount=0,
                    approved=False,
                    deleted=False,
                ),
            ]
        )
        session.commit()
    return engine


def _order(
    status: OrderStatus = OrderStatus.PENDING,
    products: list[Product] | None = None,
    order_number: str | None = "112-ABC",
    transaction_id: str = TRANSACTION_ID,
    reconciled: bool = False,
) -> Order:
    return Order(
        transaction_id=transaction_id,
        order_number=order_number,
        overall_cost=Decimal("20.00"),
        total_tax=Decimal("1.50"),
        tip=None,
        total_amount=Decimal("21.50"),
        status=status,
        reconciled=reconciled,
        products=products
        if products is not None
        else [Product(name="Coffee", price=Decimal("10.00"), quantity=2)],
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
        assert record.reconciled is False

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
    first_id = repo.upsert_order(_order(status=OrderStatus.PENDING))
    second_id = repo.upsert_order(
        _order(
            status=OrderStatus.COMPLETED,
            products=[Product(name="Tea", price=Decimal("5.00"), quantity=1)],
        )
    )

    # Same transaction -> same stable UUID, updated in place.
    assert first_id == second_id

    with Session(db) as session:
        record = session.get(OrderRecord, second_id)
        assert record.status == OrderStatus.COMPLETED.value

        items = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == second_id)
            )
            .scalars()
            .all()
        )
        assert len(items) == 1
        assert items[0].name == "Tea"


def test_transaction_id_alone_is_the_idempotency_key(db):
    """A different order number on the same charge is still the same order."""
    repo = OrderPostgresRepo(db)
    first_id = repo.upsert_order(_order(order_number="112-ABC"))
    second_id = repo.upsert_order(_order(order_number="999-ZZZ"))

    assert first_id == second_id

    with Session(db) as session:
        orders = session.execute(select(OrderRecord)).scalars().all()
        assert len(orders) == 1
        assert orders[0].order_number == "999-ZZZ"


def test_order_number_is_optional(db):
    repo = OrderPostgresRepo(db)
    order_id = repo.upsert_order(_order(order_number=None))

    with Session(db) as session:
        assert session.get(OrderRecord, order_id).order_number is None


def test_reconciled_is_persisted(db):
    repo = OrderPostgresRepo(db)
    order_id = repo.upsert_order(_order(reconciled=True))

    with Session(db) as session:
        assert session.get(OrderRecord, order_id).reconciled is True


def test_external_id_is_persisted(db):
    repo = OrderPostgresRepo(db)
    order_id = repo.upsert_order(
        _order(
            products=[
                Product(
                    name="Coffee",
                    price=Decimal("10.00"),
                    quantity=2,
                    external_id="SKU-1",
                )
            ]
        )
    )

    with Session(db) as session:
        item = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .one()
        )
        assert item.external_id == "SKU-1"


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
        Product(name="Coffee", price=Decimal("10.00"), quantity=2),
        Product(name="Tea", price=Decimal("5.00"), quantity=1),
    ]

    first_id = repo.upsert_order(
        _order(transaction_id=TRANSACTION_ID, products=shared)
    )
    second_id = repo.upsert_order(
        _order(transaction_id=OTHER_TRANSACTION_ID, products=shared)
    )

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
    order_id = repo.upsert_order(
        _order(
            products=[
                Product(
                    name="Coffee",
                    price=Decimal("10.00"),
                    quantity=2,
                    category_id="cat-abc",
                )
            ]
        )
    )

    with Session(db) as session:
        item = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .one()
        )
        assert item.category_id == "cat-abc"


def test_reingest_preserves_category_matched_on_external_id(db):
    """A re-upload must not wipe categories a categorizer already assigned."""
    repo = OrderPostgresRepo(db)
    repo.upsert_order(
        _order(
            products=[
                Product(
                    name="Coffee",
                    price=Decimal("10.00"),
                    quantity=2,
                    external_id="SKU-1",
                    category_id="cat-abc",
                )
            ]
        )
    )

    # Re-ingest carries no category, and the vendor renamed the line item.
    order_id = repo.upsert_order(
        _order(
            products=[
                Product(
                    name="Coffee (12oz)",
                    price=Decimal("10.00"),
                    quantity=2,
                    external_id="SKU-1",
                )
            ]
        )
    )

    with Session(db) as session:
        item = (
            session.execute(
                select(OrderItemRecord).where(OrderItemRecord.order_id == order_id)
            )
            .scalars()
            .one()
        )
        assert item.name == "Coffee (12oz)"
        assert item.category_id == "cat-abc"


def test_reingest_preserves_category_matched_on_name(db):
    repo = OrderPostgresRepo(db)
    repo.upsert_order(
        _order(
            products=[
                Product(
                    name="Coffee",
                    price=Decimal("10.00"),
                    quantity=2,
                    category_id="cat-abc",
                )
            ]
        )
    )
    order_id = repo.upsert_order(
        _order(products=[Product(name="Coffee", price=Decimal("10.00"), quantity=2)])
    )

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
