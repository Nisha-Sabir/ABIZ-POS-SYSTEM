"""add owner_id for data isolation

Revision ID: 20260707_0007
Revises: 20260706_0006
Create Date: 2026-07-07 08:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260707_0007"
down_revision: str | None = "20260706_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add owner_id to products table (nullable so existing products keep working)
    op.add_column(
        "products",
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_products_owner_id", "products", ["owner_id"])

    # Add created_by_id to sales table (nullable so existing sales keep working)
    op.add_column(
        "sales",
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_sales_created_by_id", "sales", ["created_by_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_created_by_id", table_name="sales")
    op.drop_column("sales", "created_by_id")
    op.drop_index("ix_products_owner_id", table_name="products")
    op.drop_column("products", "owner_id")
