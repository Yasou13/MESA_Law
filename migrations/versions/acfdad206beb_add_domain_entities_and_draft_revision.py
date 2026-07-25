"""Add Domain Entities and Draft Revision

Revision ID: acfdad206beb
Revises: f1a2b3c4d5e6
Create Date: 2026-07-26 00:40:10.679162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acfdad206beb'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # draft_revisions table
    op.create_table('draft_revisions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('draft_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['firms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_draft_revisions_draft_id'), 'draft_revisions', ['draft_id'], unique=False)
    op.create_index(op.f('ix_draft_revisions_tenant_id'), 'draft_revisions', ['tenant_id'], unique=False)

    # matter_events table
    op.create_table('matter_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('matter_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('event_date', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['matter_id'], ['matters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['firms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_matter_events_matter_id'), 'matter_events', ['matter_id'], unique=False)
    op.create_index(op.f('ix_matter_events_tenant_id'), 'matter_events', ['tenant_id'], unique=False)

    # claim_evidence_links table
    op.create_table('claim_evidence_links',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('claim_id', sa.String(), nullable=False),
        sa.Column('evidence_id', sa.String(), nullable=False),
        sa.Column('support_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['firms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_evidence_links_claim_id'), 'claim_evidence_links', ['claim_id'], unique=False)
    op.create_index(op.f('ix_claim_evidence_links_evidence_id'), 'claim_evidence_links', ['evidence_id'], unique=False)
    op.create_index(op.f('ix_claim_evidence_links_tenant_id'), 'claim_evidence_links', ['tenant_id'], unique=False)

    # review_items table
    op.create_table('review_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('matter_id', sa.String(), nullable=False),
        sa.Column('item_type', sa.String(), nullable=False),
        sa.Column('payload', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['matter_id'], ['matters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['firms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_review_items_matter_id'), 'review_items', ['matter_id'], unique=False)
    op.create_index(op.f('ix_review_items_tenant_id'), 'review_items', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_review_items_tenant_id'), table_name='review_items')
    op.drop_index(op.f('ix_review_items_matter_id'), table_name='review_items')
    op.drop_table('review_items')

    op.drop_index(op.f('ix_claim_evidence_links_tenant_id'), table_name='claim_evidence_links')
    op.drop_index(op.f('ix_claim_evidence_links_evidence_id'), table_name='claim_evidence_links')
    op.drop_index(op.f('ix_claim_evidence_links_claim_id'), table_name='claim_evidence_links')
    op.drop_table('claim_evidence_links')

    op.drop_index(op.f('ix_matter_events_tenant_id'), table_name='matter_events')
    op.drop_index(op.f('ix_matter_events_matter_id'), table_name='matter_events')
    op.drop_table('matter_events')

    op.drop_index(op.f('ix_draft_revisions_tenant_id'), table_name='draft_revisions')
    op.drop_index(op.f('ix_draft_revisions_draft_id'), table_name='draft_revisions')
    op.drop_table('draft_revisions')
