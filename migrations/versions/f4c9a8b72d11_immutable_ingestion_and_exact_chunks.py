"""make ingestion immutable and chunk provenance deterministic

Revision ID: f4c9a8b72d11
Revises: e8b6f310c4d2
Create Date: 2026-08-01 23:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4c9a8b72d11"
down_revision: str | Sequence[str] | None = "e8b6f310c4d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_revisions",
        sa.Column("quarantine_key", sa.String(), nullable=True),
    )
    op.add_column(
        "document_revisions",
        sa.Column(
            "is_canonical", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    op.add_column(
        "document_revisions",
        sa.Column("immutable_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document_revisions", sa.Column("failure_reason", sa.String(), nullable=True)
    )
    op.alter_column("document_revisions", "s3_key", nullable=True)
    op.alter_column(
        "document_revisions",
        "file_hash",
        existing_type=sa.String(),
        type_=sa.String(length=64),
        existing_nullable=True,
    )

    op.execute(
        sa.text(
            """
            UPDATE document_revisions
            SET is_canonical = CASE
                    WHEN scan_status IN (
                        'CLEAN', 'PARSING', 'OCR_REQUIRED', 'OCR_RUNNING',
                        'PARSED', 'EXTRACTION_PENDING', 'READY'
                    ) AND s3_key IS NOT NULL AND file_hash IS NOT NULL THEN true
                    ELSE false
                END,
                immutable_at = CASE
                    WHEN scan_status IN (
                        'CLEAN', 'PARSING', 'OCR_REQUIRED', 'OCR_RUNNING',
                        'PARSED', 'EXTRACTION_PENDING', 'READY'
                    ) AND s3_key IS NOT NULL AND file_hash IS NOT NULL
                    THEN COALESCE(updated_at, created_at)
                    ELSE NULL
                END,
                quarantine_key = CASE
                    WHEN scan_status IN (
                        'CLEAN', 'PARSING', 'OCR_REQUIRED', 'OCR_RUNNING',
                        'PARSED', 'EXTRACTION_PENDING', 'READY'
                    ) AND s3_key IS NOT NULL AND file_hash IS NOT NULL THEN NULL
                    ELSE s3_key
                END,
                s3_key = CASE
                    WHEN scan_status IN (
                        'CLEAN', 'PARSING', 'OCR_REQUIRED', 'OCR_RUNNING',
                        'PARSED', 'EXTRACTION_PENDING', 'READY'
                    ) AND s3_key IS NOT NULL AND file_hash IS NOT NULL THEN s3_key
                    ELSE NULL
                END,
                failure_reason = CASE
                    WHEN scan_status IN ('INFECTED', 'QUARANTINED', 'FAILED', 'BLOCKED')
                    THEN 'Legacy non-canonical revision; original reason unavailable'
                    ELSE NULL
                END
            """
        )
    )
    op.create_index(
        "ix_document_revisions_quarantine_key",
        "document_revisions",
        ["quarantine_key"],
        unique=True,
    )
    op.create_index(
        "ix_document_revisions_is_canonical",
        "document_revisions",
        ["is_canonical"],
    )
    op.create_check_constraint(
        "ck_document_revision_canonical_storage",
        "document_revisions",
        "NOT is_canonical OR (s3_key IS NOT NULL AND file_hash IS NOT NULL AND immutable_at IS NOT NULL)",
    )

    op.add_column(
        "parsed_documents",
        sa.Column(
            "provenance_state",
            sa.String(),
            server_default="LOW_PROVENANCE",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_parsed_documents_provenance_state",
        "parsed_documents",
        ["provenance_state"],
    )
    op.execute(
        sa.text(
            """
            UPDATE parsed_documents AS parsed
            SET provenance_state = CASE
                WHEN revision.mime_type = 'application/pdf'
                     AND parsed.parser_used NOT IN ('mock', 'legacy')
                THEN 'VERIFIED_PDF'
                ELSE 'LOW_PROVENANCE'
            END
            FROM document_revisions AS revision
            WHERE revision.id = parsed.revision_id
            """
        )
    )

    # Preserve every legacy parse while making its run number unique.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT id,
                       row_number() OVER (
                           PARTITION BY revision_id
                           ORDER BY created_at, id
                       ) AS run_number
                FROM parsed_documents
            )
            UPDATE parsed_documents AS parsed
            SET parsing_revision = ranked.run_number
            FROM ranked
            WHERE parsed.id = ranked.id
            """
        )
    )
    op.create_unique_constraint(
        "uq_parsed_document_revision_run",
        "parsed_documents",
        ["revision_id", "parsing_revision"],
    )

    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT id,
                       row_number() OVER (
                           PARTITION BY revision_id, page_id
                           ORDER BY chunk_index, created_at, id
                       ) - 1 AS stable_index
                FROM document_chunks
                WHERE revision_id IS NOT NULL
            )
            UPDATE document_chunks AS chunk
            SET chunk_index = ranked.stable_index
            FROM ranked
            WHERE chunk.id = ranked.id
            """
        )
    )
    op.create_unique_constraint(
        "uq_document_chunk_span",
        "document_chunks",
        ["revision_id", "page_id", "chunk_index"],
    )
    op.create_check_constraint(
        "ck_document_chunk_offsets",
        "document_chunks",
        "character_start IS NULL OR character_end > character_start",
    )
    op.create_check_constraint(
        "ck_source_locator_offsets",
        "source_locators",
        "character_start IS NULL OR character_end > character_start",
    )
    op.create_check_constraint(
        "ck_verified_pdf_locator",
        "source_locators",
        "provenance_state NOT LIKE 'VERIFIED_PDF%' OR "
        "(document_revision_id IS NOT NULL AND parsed_page_id IS NOT NULL "
        "AND chunk_id IS NOT NULL AND page_number > 0 "
        "AND evidence_sha256 IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_verified_pdf_locator", "source_locators", type_="check")
    op.drop_constraint("ck_source_locator_offsets", "source_locators", type_="check")
    op.drop_constraint("ck_document_chunk_offsets", "document_chunks", type_="check")
    op.drop_constraint("uq_document_chunk_span", "document_chunks", type_="unique")
    op.drop_constraint(
        "uq_parsed_document_revision_run", "parsed_documents", type_="unique"
    )
    op.drop_index("ix_parsed_documents_provenance_state", table_name="parsed_documents")
    op.drop_column("parsed_documents", "provenance_state")

    op.drop_constraint(
        "ck_document_revision_canonical_storage",
        "document_revisions",
        type_="check",
    )
    op.drop_index("ix_document_revisions_is_canonical", table_name="document_revisions")
    op.drop_index(
        "ix_document_revisions_quarantine_key", table_name="document_revisions"
    )
    op.execute(
        sa.text(
            """
            UPDATE document_revisions
            SET s3_key = COALESCE(
                s3_key,
                quarantine_key,
                'legacy-unavailable/' || id
            )
            """
        )
    )
    op.alter_column(
        "document_revisions",
        "file_hash",
        existing_type=sa.String(length=64),
        type_=sa.String(),
        existing_nullable=True,
    )
    op.alter_column("document_revisions", "s3_key", nullable=False)
    for column in (
        "failure_reason",
        "immutable_at",
        "is_canonical",
        "quarantine_key",
    ):
        op.drop_column("document_revisions", column)
