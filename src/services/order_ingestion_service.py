from decimal import Decimal
import uuid

from loguru import logger

from src.interfaces.order_repo import OrderRepoInterface
from src.models.budget import Transaction
from src.models.order import ExtractedOrder, Order

MILLIUNITS = 1000


def _to_milliunits(value: Decimal | None) -> int:
    if value is None:
        return 0
    return int((value * MILLIUNITS).to_integral_value())


class OrderIngestionService:
    """The single place an order is written.

    Both the reconciliation check and the promotion from ``ExtractedOrder`` to
    ``Order`` live here so that every ingestion path -- today the invoice
    upload, later email -- produces rows with the same guarantees.
    """

    def __init__(self, order_repo: OrderRepoInterface):
        self.order_repo = order_repo

    def ingest(
        self, extracted: ExtractedOrder, transaction: Transaction
    ) -> uuid.UUID:
        """Persist an extracted order against its matched transaction."""
        reconciled = self.reconciles(extracted, transaction)
        if not reconciled:
            logger.warning(
                f"Order for transaction {transaction.id} does not reconcile: "
                f"line items total {self.line_item_total(extracted)} milliunits "
                f"against a charge of {abs(transaction.amount)}"
            )

        order = Order.from_extracted(
            extracted, transaction_id=transaction.id, reconciled=reconciled
        )
        return self.order_repo.upsert_order(order)

    def line_item_total(self, extracted: ExtractedOrder) -> int:
        """Milliunit total the line items imply, including tax and tip."""
        items = sum(
            _to_milliunits(product.price) * product.quantity
            for product in extracted.products
        )
        return items + _to_milliunits(extracted.total_tax) + _to_milliunits(
            extracted.tip
        )

    def reconciles(
        self, extracted: ExtractedOrder, transaction: Transaction
    ) -> bool:
        """Whether the line items account for the whole charge.

        YNAB records outflows as negative milliunits while invoice totals are
        positive, so the comparison is on absolute value. An order that fails
        this must not be split across YNAB categories downstream -- the
        sub-amounts would not sum to the transaction.
        """
        return self.line_item_total(extracted) == abs(transaction.amount)
