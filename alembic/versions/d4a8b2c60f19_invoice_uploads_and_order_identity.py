"""invoice uploads table and transaction-keyed order identity

Revision ID: d4a8b2c60f19
Revises: c3f7a1e9b204
Create Date: 2026-07-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4a8b2c60f19"
down_revision: str | Sequence[str] | None = "c3f7a1e9b204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # One posted card charge is one order, so the transaction alone is the
    # idempotency key; order_number becomes vendor metadata.
    op.drop_constraint(
        "uq_orders_transaction_order_number", "orders", type_="unique"
    )
    op.create_unique_constraint(
        "uq_orders_transaction_id", "orders", ["transaction_id"]
    )
    op.alter_column("orders", "order_number", nullable=True)
    op.add_column(
        "orders",
        sa.Column(
            "reconciled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "order_items", sa.Column("external_id", sa.String(), nullable=True)
    )

    op.create_table(
        "invoice_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False, unique=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("extracted_order", postgresql.JSONB(), nullable=True),
        sa.Column(
            "transaction_id",
            sa.String(),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_invoice_uploads_content_hash", "invoice_uploads", ["content_hash"]
    )
    op.create_index("ix_invoice_uploads_status", "invoice_uploads", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_invoice_uploads_status", table_name="invoice_uploads")
    op.drop_index("ix_invoice_uploads_content_hash", table_name="invoice_uploads")
    op.drop_table("invoice_uploads")

    op.drop_column("order_items", "external_id")

    op.drop_column("orders", "reconciled")
    op.alter_column("orders", "order_number", nullable=False)
    op.drop_constraint("uq_orders_transaction_id", "orders", type_="unique")
    op.create_unique_constraint(
        "uq_orders_transaction_order_number",
        "orders",
        ["transaction_id", "order_number"],
    )
