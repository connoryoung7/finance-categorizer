from datetime import datetime
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TransactionRecord(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str | None] = mapped_column(String, nullable=True)
    account_name: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    memo: Mapped[str | None] = mapped_column(String, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    payee_name: Mapped[str | None] = mapped_column(String, nullable=True)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    category_name: Mapped[str | None] = mapped_column(String, nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class OrderRecord(Base):
    __tablename__ = "orders"
    __table_args__ = (
        # One posted card charge is one order, so the transaction alone is the
        # idempotency key. ``order_number`` is vendor metadata: a vendor order
        # split across shipments produces several charges that all carry it.
        UniqueConstraint("transaction_id", name="uq_orders_transaction_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[str] = mapped_column(
        String, ForeignKey("transactions.id"), nullable=False
    )
    order_number: Mapped[str | None] = mapped_column(String, nullable=True)
    overall_cost: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_tax: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tip: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    # False when the line items do not sum to the matched transaction amount.
    reconciled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItemRecord"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrderItemRecord(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "line_number",
            name="uq_order_items_order_line_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Vendor line-item identifier (SKU, ASIN, item code) when the invoice has one.
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # YNAB category id, assigned later by a categorization step; used downstream
    # to decide whether a transaction should be split across categories.
    # Line items are delete-and-replace on re-ingest, so the repo carries this
    # value forward, matching on external_id then name.
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    order: Mapped["OrderRecord"] = relationship(back_populates="items")


class InvoiceUploadRecord(Base):
    """An uploaded invoice PDF and the outcome of processing it.

    Uploads are accepted synchronously and processed by a Celery task, so this
    row is the only record of what happened -- the endpoint returns nothing
    beyond the id.
    """

    __tablename__ = "invoice_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    # SHA-256 of the uploaded bytes. The transaction is unknown at accept time,
    # so this is what makes re-uploading the same file a no-op.
    content_hash: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    # Kept so that re-matching an unmatched upload never re-runs the LLM.
    extracted_order: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("transactions.id"), nullable=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SyncState(Base):
    __tablename__ = "sync_state"

    budget_id: Mapped[str] = mapped_column(String, primary_key=True)
    last_knowledge_of_server: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
