"""Merge heads for RLS and phase 5 changes

Revision ID: c352dad29efc
Revises: 0fb531054f20, 39e9a5e1a894
Create Date: 2026-07-27 11:10:16.774630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c352dad29efc'
down_revision: Union[str, Sequence[str], None] = ('0fb531054f20', '39e9a5e1a894')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
