"""Add is_active to Membership

Revision ID: 97a1b2c3d4e5
Revises: 860d9f8565ad
Create Date: 2026-07-25 20:00:00.000000

"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '97a1b2c3d4e5'
down_revision: str | Sequence[str] | None = '860d9f8565ad'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('memberships', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_column('memberships', 'is_active')
