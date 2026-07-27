"""create orders and order_items tables

Revision ID: c3f7a1e9b204
Revises: b5786a456473
Create Date: 2026-07-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f7a1e9b204"
down_revision: str | Sequence[str] | None = "b5786a456473"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.String(),
            sa.ForeignKey("transactions.id"),
            nullable=False,
        ),
        sa.Column("order_number", sa.String(), nullable=False),
        sa.Column("overall_cost", sa.BigInteger(), nullable=False),
        sa.Column("total_tax", sa.BigInteger(), nullable=False),
        sa.Column("tip", sa.BigInteger(), nullable=True),
        sa.Column("total_amount", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
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
        sa.UniqueConstraint(
            "transaction_id",
            "order_number",
            name="uq_orders_transaction_order_number",
        ),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("order_items")
    op.drop_table("orders")
