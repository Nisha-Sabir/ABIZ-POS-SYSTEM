"""add offline sale sync fields

Revision ID: 20260616_0005
Revises: 20260613_0004
Create Date: 2026-06-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260616_0005"
down_revision: Union[str, None] = "20260613_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("client_sale_id", sa.String(length=64), nullable=True))
    op.add_column("sales", sa.Column("source", sa.String(length=32), nullable=False, server_default="online"))
    op.create_index(op.f("ix_sales_client_sale_id"), "sales", ["client_sale_id"], unique=True)
    op.alter_column("sales", "source", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_sales_client_sale_id"), table_name="sales")
    op.drop_column("sales", "source")
    op.drop_column("sales", "client_sale_id")
