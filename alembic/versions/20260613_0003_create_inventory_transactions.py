"""create inventory transactions

Revision ID: 20260613_0003
Revises: 20260613_0002
Create Date: 2026-06-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260613_0003"
down_revision: Union[str, None] = "20260613_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    transaction_type = postgresql.ENUM(
        "stock_in",
        "stock_out",
        name="inventory_transaction_type",
        create_type=False,
    )
    sa.Enum("stock_in", "stock_out", name="inventory_transaction_type").create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inventory_transactions_created_at"),
        "inventory_transactions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_transactions_created_by"),
        "inventory_transactions",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_transactions_id"),
        "inventory_transactions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_transactions_product_id"),
        "inventory_transactions",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_transactions_transaction_type"),
        "inventory_transactions",
        ["transaction_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_transactions_transaction_type"), table_name="inventory_transactions")
    op.drop_index(op.f("ix_inventory_transactions_product_id"), table_name="inventory_transactions")
    op.drop_index(op.f("ix_inventory_transactions_id"), table_name="inventory_transactions")
    op.drop_index(op.f("ix_inventory_transactions_created_by"), table_name="inventory_transactions")
    op.drop_index(op.f("ix_inventory_transactions_created_at"), table_name="inventory_transactions")
    op.drop_table("inventory_transactions")

    sa.Enum(name="inventory_transaction_type").drop(op.get_bind(), checkfirst=True)
