"""harden legal jobs and retire outbox execution

Revision ID: e8b6f310c4d2
Revises: d7a4c2e91b30
Create Date: 2026-08-01 22:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8b6f310c4d2"
down_revision: str | Sequence[str] | None = "d7a4c2e91b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "legal_jobs",
        sa.Column("attempts_made", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "legal_jobs", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "legal_jobs",
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("legal_jobs", sa.Column("lease_token", sa.String(), nullable=True))
    op.add_column("legal_jobs", sa.Column("requested_by", sa.String(), nullable=True))
    op.add_column(
        "legal_jobs", sa.Column("idempotency_key", sa.String(), nullable=True)
    )
    op.add_column("legal_jobs", sa.Column("error_class", sa.String(), nullable=True))
    op.add_column(
        "legal_job_attempts", sa.Column("lease_token", sa.String(), nullable=True)
    )

    op.execute(
        sa.text(
            """
            UPDATE legal_jobs
            SET attempts_made = GREATEST(max_retries - retries, 0),
                status = CASE lower(status)
                    WHEN 'pending' THEN 'PENDING'
                    WHEN 'processing' THEN 'RUNNING'
                    WHEN 'completed' THEN 'SUCCEEDED'
                    WHEN 'failed' THEN 'FAILED'
                    WHEN 'dead' THEN 'DEAD'
                    ELSE 'FAILED'
                END
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE legal_job_attempts
            SET status = CASE lower(status)
                WHEN 'processing' THEN 'RUNNING'
                WHEN 'running' THEN 'RUNNING'
                WHEN 'completed' THEN 'SUCCEEDED'
                WHEN 'success' THEN 'SUCCEEDED'
                WHEN 'succeeded' THEN 'SUCCEEDED'
                WHEN 'failed' THEN 'FAILED'
                ELSE upper(status)
            END
            """
        )
    )
    op.alter_column("legal_jobs", "status", server_default="PENDING", nullable=False)
    op.alter_column("legal_jobs", "max_retries", server_default="3", nullable=False)
    op.alter_column("legal_jobs", "retries", server_default="3", nullable=False)

    op.create_index("ix_legal_jobs_lease_token", "legal_jobs", ["lease_token"])
    op.create_index("ix_legal_jobs_requested_by", "legal_jobs", ["requested_by"])
    op.create_index(
        "uq_legal_jobs_idempotency",
        "legal_jobs",
        ["tenant_id", "type", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_check_constraint(
        "ck_legal_jobs_status",
        "legal_jobs",
        "status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'DEAD')",
    )

    op.execute(
        sa.text(
            """
            INSERT INTO legal_jobs (
                id, created_at, updated_at, version_id, is_deleted, legal_hold,
                type, payload, status, tenant_id, matter_id, max_retries,
                retries, attempts_made, run_at
            )
            SELECT
                'outbox-' || id, created_at, updated_at, 1, false, false,
                event_type, payload, 'PENDING', payload->>'tenant_id',
                payload->>'matter_id', 3, 3, 0, created_at
            FROM legal_outbox
            WHERE lower(status) = 'pending'
              AND payload::jsonb ? 'tenant_id'
              AND payload::jsonb ? 'matter_id'
              AND event_type IN (
                  'SCAN_DOCUMENT', 'PARSE_DOCUMENT', 'OCR_DOCUMENT',
                  'EXTRACT_LEGAL_DATA', 'EXTRACT_LEGAL_FACTS',
                  'BUILD_LEXICAL_INDEX', 'SYNC_MESA_DOCUMENT',
                  'PUBLISH_REVIEW', 'EXPORT_DRAFT'
              )
            ON CONFLICT (id) DO NOTHING
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE legal_outbox
            SET status = CASE
                WHEN ('outbox-' || id) IN (SELECT id FROM legal_jobs)
                    THEN 'migrated'
                ELSE 'legacy_unmigrated'
            END
            WHERE lower(status) = 'pending'
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("ck_legal_jobs_status", "legal_jobs", type_="check")
    op.drop_index("uq_legal_jobs_idempotency", table_name="legal_jobs")
    op.drop_index("ix_legal_jobs_requested_by", table_name="legal_jobs")
    op.drop_index("ix_legal_jobs_lease_token", table_name="legal_jobs")
    op.execute(
        sa.text(
            """
            UPDATE legal_jobs
            SET status = CASE status
                WHEN 'PENDING' THEN 'pending'
                WHEN 'RUNNING' THEN 'processing'
                WHEN 'SUCCEEDED' THEN 'completed'
                WHEN 'FAILED' THEN 'failed'
                WHEN 'DEAD' THEN 'dead'
                ELSE lower(status)
            END
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE legal_job_attempts
            SET status = CASE status
                WHEN 'RUNNING' THEN 'processing'
                WHEN 'SUCCEEDED' THEN 'completed'
                WHEN 'FAILED' THEN 'failed'
                WHEN 'LOST_LEASE' THEN 'failed'
                ELSE lower(status)
            END
            """
        )
    )
    for column in (
        "error_class",
        "idempotency_key",
        "requested_by",
        "lease_token",
        "heartbeat_at",
        "locked_at",
        "attempts_made",
    ):
        op.drop_column("legal_jobs", column)
    op.drop_column("legal_job_attempts", "lease_token")
