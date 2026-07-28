"""add_review_state_enum

Revision ID: 1dc95c6dc781
Revises: 07b5116bdc26
Create Date: 2026-07-28 09:56:09.460130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dc95c6dc781'
down_revision: Union[str, Sequence[str], None] = '07b5116bdc26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum
    op.execute("CREATE TYPE review_state AS ENUM ('PENDING', 'IN_REVIEW', 'APPROVED_PENDING_PUBLICATION', 'PUBLISHED', 'REJECTED', 'DUPLICATE', 'PUBLICATION_FAILED', 'CANCELLED')")
    
    # Map old values
    op.execute("UPDATE review_items SET status = 'PENDING' WHERE status IN ('draft', 'pending')")
    op.execute("UPDATE review_items SET status = 'APPROVED_PENDING_PUBLICATION' WHERE status IN ('approved', 'corrected')")
    op.execute("UPDATE review_items SET status = 'REJECTED' WHERE status = 'rejected'")
    op.execute("UPDATE review_items SET status = 'PENDING' WHERE status NOT IN ('PENDING', 'APPROVED_PENDING_PUBLICATION', 'REJECTED')")
    
    # Cast column
    op.execute("ALTER TABLE review_items ALTER COLUMN status TYPE review_state USING status::review_state")


def downgrade() -> None:
    op.execute("ALTER TABLE review_items ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR")
    op.execute("DROP TYPE review_state")
