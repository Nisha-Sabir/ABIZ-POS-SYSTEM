"""add low_stock_threshold to products

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-06 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260706_0006'
down_revision: Union[str, None] = '20260616_0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # add column
    op.add_column('products', sa.Column('low_stock_threshold', sa.Integer(), server_default='10', nullable=False))


def downgrade() -> None:
    # drop column
    op.drop_column('products', 'low_stock_threshold')
