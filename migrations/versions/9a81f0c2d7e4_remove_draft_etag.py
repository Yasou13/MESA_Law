"""Remove the redundant draft ETag column.

Revision ID: 9a81f0c2d7e4
Revises: a1d7e3c90b42
Create Date: 2026-10-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a81f0c2d7e4"
down_revision: Union[str, Sequence[str], None] = "a1d7e3c90b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("drafts", "etag")


def downgrade() -> None:
    op.add_column("drafts", sa.Column("etag", sa.String(), nullable=True))
    op.execute("UPDATE drafts SET etag = 'v' || version::text")
    op.alter_column("drafts", "etag", nullable=False)
