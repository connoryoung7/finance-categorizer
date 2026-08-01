from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, PositiveInt


class OrderStatus(str, Enum):
    """Lifecycle state of an order as reported by the vendor's invoice."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Product(BaseModel):
    name: str
    price: Decimal = Field(..., ge=0)
    quantity: PositiveInt
    # Vendor line-item identifier (SKU, ASIN, item code) when the invoice carries
    # one. Used to re-match line items to their categories across re-ingest.
    external_id: str | None = None
    # YNAB category id, assigned later by a categorization step (NULL at ingest).
    category_id: str | None = None


class ExtractedOrder(BaseModel):
    """An order as read off an invoice, before it is matched to a transaction.

    Extraction happens before matching, so this deliberately has no
    ``transaction_id``. :meth:`Order.from_extracted` promotes it once a
    transaction is known.
    """

    order_number: str | None = None
    overall_cost: Decimal = Field(..., ge=0)
    total_tax: Decimal = Field(..., ge=0)
    tip: Decimal | None = Field(default=None, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    status: OrderStatus = OrderStatus.COMPLETED
    products: list[Product]

    # Used to narrow the transaction search and dropped afterwards. These are
    # not columns on ``orders`` -- they survive in the upload's stored JSONB so
    # that re-matching never has to re-run extraction.
    order_date: date | None = None
    vendor_name: str | None = None


class Order(BaseModel):
    id: UUID | None = None
    transaction_id: str
    order_number: str | None = None
    overall_cost: Decimal = Field(..., ge=0)
    total_tax: Decimal = Field(..., ge=0)
    tip: Decimal | None = Field(default=None, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    status: OrderStatus
    # False when the line items do not sum to the matched transaction amount.
    # Downstream categorization must skip unreconciled orders rather than push
    # an invalid split to YNAB.
    reconciled: bool = False
    products: list[Product]

    @classmethod
    def from_extracted(
        cls,
        extracted: ExtractedOrder,
        transaction_id: str,
        reconciled: bool,
    ) -> "Order":
        """Promote an extracted order to a persistable one.

        ``order_date`` and ``vendor_name`` exist only to drive matching and have
        no column on ``orders``, so they are dropped here rather than carried as
        fields the repository silently ignores.
        """
        return cls(
            transaction_id=transaction_id,
            reconciled=reconciled,
            **extracted.model_dump(exclude={"order_date", "vendor_name"}),
        )
