"""enforce reviewed publication and sourced QA contracts

Revision ID: a1d7e3c90b42
Revises: f4c9a8b72d11
Create Date: 2026-08-02 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1d7e3c90b42"
down_revision: str | Sequence[str] | None = "f4c9a8b72d11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REVIEW_STATES = (
    "PROPOSED",
    "APPROVED",
    "CORRECTED",
    "REJECTED",
    "PUBLISHING",
    "PUBLISHED",
    "PUBLICATION_FAILED",
)


def upgrade() -> None:
    op.execute("ALTER TABLE review_items ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE review_items ALTER COLUMN status TYPE VARCHAR(32) "
        "USING status::text"
    )
    op.execute("DROP TYPE IF EXISTS review_state")
    op.execute(
        sa.text(
            """
            UPDATE review_items
            SET status = CASE status
                WHEN 'PENDING' THEN 'PROPOSED'
                WHEN 'IN_REVIEW' THEN 'PROPOSED'
                WHEN 'APPROVED_PENDING_PUBLICATION' THEN 'APPROVED'
                WHEN 'DUPLICATE' THEN 'REJECTED'
                WHEN 'CANCELLED' THEN 'REJECTED'
                ELSE status
            END
            """
        )
    )
    op.alter_column("review_items", "status", server_default="PROPOSED", nullable=False)
    op.create_check_constraint(
        "ck_review_item_state",
        "review_items",
        f"status IN ({', '.join(repr(state) for state in REVIEW_STATES)})",
    )
    op.add_column(
        "review_items", sa.Column("decision_reason", sa.String(), nullable=True)
    )

    op.add_column(
        "legal_assertions", sa.Column("review_id", sa.String(), nullable=True)
    )
    op.add_column(
        "legal_assertions", sa.Column("review_version", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_legal_assertions_review_id",
        "legal_assertions",
        "review_items",
        ["review_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_legal_assertions_review_id",
        "legal_assertions",
        ["review_id"],
        unique=True,
    )
    op.create_check_constraint(
        "ck_reviewed_legal_assertion_typed",
        "legal_assertions",
        "canonical_status != 'REVIEWED' OR "
        "(assertion_type IS NOT NULL AND subject_text IS NOT NULL "
        "AND predicate IS NOT NULL AND object_text IS NOT NULL "
        "AND source_locator_id IS NOT NULL AND review_id IS NOT NULL)",
    )

    op.add_column(
        "mesa_sync_records", sa.Column("session_id", sa.String(), nullable=True)
    )
    op.create_index(
        "ix_mesa_sync_records_session_id", "mesa_sync_records", ["session_id"]
    )

    # Legacy unreviewed document sync is no longer an executable publication path.
    op.execute(
        sa.text(
            """
            UPDATE legal_jobs
            SET status = 'FAILED',
                error_class = 'LegacyUnreviewedPublicationDisabled',
                error_message = 'Document-level MESA sync was retired; publish reviewed assertions instead',
                lease_token = NULL,
                locked_at = NULL,
                locked_until = NULL,
                heartbeat_at = NULL
            WHERE type = 'SYNC_MESA_DOCUMENT'
              AND status IN ('PENDING', 'RUNNING')
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_mesa_sync_records_session_id", table_name="mesa_sync_records")
    op.drop_column("mesa_sync_records", "session_id")

    op.drop_constraint(
        "ck_reviewed_legal_assertion_typed", "legal_assertions", type_="check"
    )
    op.drop_index("ix_legal_assertions_review_id", table_name="legal_assertions")
    op.drop_constraint(
        "fk_legal_assertions_review_id", "legal_assertions", type_="foreignkey"
    )
    op.drop_column("legal_assertions", "review_version")
    op.drop_column("legal_assertions", "review_id")

    op.drop_column("review_items", "decision_reason")
    op.drop_constraint("ck_review_item_state", "review_items", type_="check")
    op.execute("ALTER TABLE review_items ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "CREATE TYPE review_state AS ENUM "
        "('PENDING', 'IN_REVIEW', 'APPROVED_PENDING_PUBLICATION', 'PUBLISHED', "
        "'REJECTED', 'DUPLICATE', 'PUBLICATION_FAILED', 'CANCELLED')"
    )
    op.execute(
        sa.text(
            """
            UPDATE review_items
            SET status = CASE status
                WHEN 'PROPOSED' THEN 'PENDING'
                WHEN 'APPROVED' THEN 'APPROVED_PENDING_PUBLICATION'
                WHEN 'CORRECTED' THEN 'APPROVED_PENDING_PUBLICATION'
                WHEN 'PUBLISHING' THEN 'APPROVED_PENDING_PUBLICATION'
                ELSE status
            END
            """
        )
    )
    op.execute(
        "ALTER TABLE review_items ALTER COLUMN status TYPE review_state "
        "USING status::review_state"
    )
