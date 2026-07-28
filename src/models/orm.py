from datetime import datetime
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
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
        UniqueConstraint(
            "transaction_id",
            "order_number",
            name="uq_orders_transaction_order_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[str] = mapped_column(
        String, ForeignKey("transactions.id"), nullable=False
    )
    order_number: Mapped[str] = mapped_column(String, nullable=False)
    overall_cost: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_tax: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tip: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
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

    # Application-provided identifier (not autoincremented). Line-item ids repeat
    # across orders, so the key is scoped to the owning order.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # YNAB category id, assigned later by a categorization step; used downstream
    # to decide whether a transaction should be split across categories.
    # NOTE: line items are delete-and-replace on re-ingest, so once a categorizer
    # populates this, re-ingesting an order will wipe it. Preservation is deferred
    # until that categorizer is built (needs a stable line-item key we don't have).
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    order: Mapped["OrderRecord"] = relationship(back_populates="items")


class SyncState(Base):
    __tablename__ = "sync_state"

    budget_id: Mapped[str] = mapped_column(String, primary_key=True)
    last_knowledge_of_server: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
