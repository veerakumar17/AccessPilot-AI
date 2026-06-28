"""add ai_simulation column to violations

Revision ID: 2a7b8c9d0e1f
Revises: a3a7dd68f6c9
Create Date: 2026-06-19 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2a7b8c9d0e1f'
down_revision: Union[str, None] = 'a3a7dd68f6c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('violations', sa.Column('ai_simulation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('violations', 'ai_simulation')