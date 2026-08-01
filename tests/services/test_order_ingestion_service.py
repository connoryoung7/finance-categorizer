from decimal import Decimal
import uuid

from src.interfaces.order_repo import OrderRepoInterface
from src.models.budget import Transaction
from src.models.order import ExtractedOrder, OrderStatus, Product
from src.services.order_ingestion_service import OrderIngestionService


class FakeOrderRepo(OrderRepoInterface):
    def __init__(self):
        self.saved = []

    def upsert_order(self, order):
        self.saved.append(order)
        return uuid.uuid4()


def _transaction(amount: int = -21500) -> Transaction:
    return Transaction(
        id="txn-1",
        payee_id=None,
        payee_name="VINAL BAKERY",
        date="2026-03-15",
        amount=amount,
        memo=None,
        category_id=None,
        category_name=None,
        approved=False,
    )


def _extracted(
    products: list[Product] | None = None,
    tax: str = "1.50",
    tip: str | None = None,
) -> ExtractedOrder:
    return ExtractedOrder(
        overall_cost=Decimal("20.00"),
        total_tax=Decimal(tax),
        tip=Decimal(tip) if tip else None,
        total_amount=Decimal("21.50"),
        products=products
        if products is not None
        else [Product(name="Coffee", price=Decimal("10.00"), quantity=2)],
    )


def test_reconciles_when_items_plus_tax_equal_the_charge():
    service = OrderIngestionService(FakeOrderRepo())
    # 2 x $10.00 + $1.50 tax = $21.50, and the charge is -21500 milliunits.
    assert service.reconciles(_extracted(), _transaction(-21500)) is True


def test_does_not_reconcile_when_totals_disagree():
    service = OrderIngestionService(FakeOrderRepo())
    assert service.reconciles(_extracted(), _transaction(-19999)) is False


def test_reconciliation_ignores_the_sign_of_the_charge():
    """YNAB records outflows negative; invoice totals are positive."""
    service = OrderIngestionService(FakeOrderRepo())
    assert service.reconciles(_extracted(), _transaction(21500)) is True


def test_tip_counts_towards_reconciliation():
    service = OrderIngestionService(FakeOrderRepo())
    extracted = _extracted(tip="3.00")
    assert service.reconciles(extracted, _transaction(-24500)) is True


def test_line_item_total_multiplies_price_by_quantity():
    service = OrderIngestionService(FakeOrderRepo())
    extracted = _extracted(
        products=[
            Product(name="Coffee", price=Decimal("10.00"), quantity=2),
            Product(name="Tea", price=Decimal("5.00"), quantity=3),
        ]
    )
    # (10.00 * 2) + (5.00 * 3) + 1.50 tax = 36.50
    assert service.line_item_total(extracted) == 36500


def test_ingest_persists_with_the_matched_transaction_and_flag():
    repo = FakeOrderRepo()
    service = OrderIngestionService(repo)

    order_id = service.ingest(_extracted(), _transaction(-21500))

    assert isinstance(order_id, uuid.UUID)
    saved = repo.saved[0]
    assert saved.transaction_id == "txn-1"
    assert saved.reconciled is True
    assert saved.status == OrderStatus.COMPLETED
    assert [product.name for product in saved.products] == ["Coffee"]


def test_ingest_still_writes_an_unreconciled_order():
    """A mismatch is recorded, not rejected -- the data is still worth keeping."""
    repo = FakeOrderRepo()
    order_id = OrderIngestionService(repo).ingest(_extracted(), _transaction(-99999))

    assert isinstance(order_id, uuid.UUID)
    assert repo.saved[0].reconciled is False


def test_matching_only_fields_are_not_carried_onto_the_order():
    repo = FakeOrderRepo()
    extracted = _extracted()
    extracted.vendor_name = "Vinal Bakery"

    OrderIngestionService(repo).ingest(extracted, _transaction())

    assert not hasattr(repo.saved[0], "vendor_name")
    assert not hasattr(repo.saved[0], "order_date")
