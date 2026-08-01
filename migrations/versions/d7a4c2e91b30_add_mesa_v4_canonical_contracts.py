"""add MESA v4 bindings, sync state, and exact provenance contracts

Revision ID: d7a4c2e91b30
Revises: c150029e598e
Create Date: 2026-08-01 21:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7a4c2e91b30"
down_revision: str | Sequence[str] | None = "c150029e598e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("version_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "legal_hold", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    ]


def _enable_tenant_rls(table_name: str) -> None:
    op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(f'DROP POLICY IF EXISTS tenant_isolation_policy ON "{table_name}"')
    )
    op.execute(
        sa.text(
            f"""
            CREATE POLICY tenant_isolation_policy ON "{table_name}"
            AS PERMISSIVE FOR ALL TO PUBLIC
            USING (tenant_id = current_setting('app.current_tenant', true)::text)
            WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::text)
            """
        )
    )
    op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))


def upgrade() -> None:
    op.create_table(
        "mesa_scope_bindings",
        *_audit_columns(),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("matter_id", sa.String(), nullable=False),
        sa.Column("mesa_tenant_id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column(
            "provisioning_status", sa.String(), server_default="PENDING", nullable=False
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["firms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "matter_id", name="uq_mesa_binding_matter"),
        sa.UniqueConstraint("tenant_id", "dataset_id", name="uq_mesa_binding_dataset"),
    )
    op.create_index(
        "ix_mesa_scope_bindings_tenant_id", "mesa_scope_bindings", ["tenant_id"]
    )
    op.create_index(
        "ix_mesa_scope_bindings_matter_id", "mesa_scope_bindings", ["matter_id"]
    )

    op.create_table(
        "mesa_sync_records",
        *_audit_columns(),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("matter_id", sa.String(), nullable=False),
        sa.Column("binding_id", sa.String(), nullable=False),
        sa.Column("source_locator_id", sa.String(), nullable=True),
        sa.Column("assertion_id", sa.String(), nullable=True),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("mutation_id", sa.String(), nullable=True),
        sa.Column("candidate_id", sa.String(), nullable=True),
        sa.Column("pipeline_run_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="PENDING", nullable=False),
        sa.Column(
            "is_terminal", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assertion_id"], ["legal_assertions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["binding_id"], ["mesa_scope_bindings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_locator_id"], ["source_locators.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["firms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "idempotency_key", name="uq_mesa_sync_idempotency"
        ),
    )
    op.create_index(
        "ix_mesa_sync_records_tenant_id", "mesa_sync_records", ["tenant_id"]
    )
    op.create_index(
        "ix_mesa_sync_records_matter_id", "mesa_sync_records", ["matter_id"]
    )
    op.create_index(
        "ix_mesa_sync_records_binding_id", "mesa_sync_records", ["binding_id"]
    )
    op.create_index(
        "ix_mesa_sync_records_mutation_id", "mesa_sync_records", ["mutation_id"]
    )

    op.add_column("source_locators", sa.Column("chunk_id", sa.String(), nullable=True))
    op.add_column(
        "source_locators", sa.Column("evidence_text", sa.Text(), nullable=True)
    )
    op.add_column(
        "source_locators",
        sa.Column("evidence_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "source_locators", sa.Column("extraction_version", sa.String(), nullable=True)
    )
    op.add_column(
        "source_locators",
        sa.Column(
            "provenance_state",
            sa.String(),
            server_default="LOW_PROVENANCE",
            nullable=False,
        ),
    )
    op.add_column(
        "source_locators",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_source_locators_chunk_id",
        "source_locators",
        "document_chunks",
        ["chunk_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_source_locators_chunk_id", "source_locators", ["chunk_id"])
    op.create_index(
        "ix_source_locators_provenance_state", "source_locators", ["provenance_state"]
    )
    op.execute(
        sa.text(
            """
            UPDATE source_locators
            SET evidence_text = text_snippet,
                evidence_sha256 = text_hash,
                extraction_version = COALESCE(parser_version, 'legacy'),
                provenance_state = 'LOW_PROVENANCE'
            """
        )
    )

    for name, column_type in (
        ("assertion_type", sa.String()),
        ("subject_text", sa.Text()),
        ("predicate", sa.String()),
        ("object_text", sa.Text()),
        ("object_data", sa.JSON()),
        ("polarity", sa.String()),
        ("modality", sa.String()),
    ):
        op.add_column("legal_assertions", sa.Column(name, column_type, nullable=True))
    op.add_column(
        "legal_assertions",
        sa.Column(
            "canonical_status",
            sa.String(),
            server_default="LEGACY_UNTYPED",
            nullable=False,
        ),
    )
    op.add_column(
        "legal_assertions",
        sa.Column(
            "publication_status",
            sa.String(),
            server_default="NOT_PUBLISHED",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_legal_assertions_assertion_type", "legal_assertions", ["assertion_type"]
    )
    op.create_index(
        "ix_legal_assertions_canonical_status", "legal_assertions", ["canonical_status"]
    )
    op.create_index(
        "ix_legal_assertions_publication_status",
        "legal_assertions",
        ["publication_status"],
    )

    op.add_column(
        "document_chunks", sa.Column("revision_id", sa.String(), nullable=True)
    )
    op.add_column(
        "document_chunks", sa.Column("character_start", sa.Integer(), nullable=True)
    )
    op.add_column(
        "document_chunks", sa.Column("character_end", sa.Integer(), nullable=True)
    )
    op.add_column(
        "document_chunks",
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "document_chunks", sa.Column("extraction_version", sa.String(), nullable=True)
    )
    op.add_column(
        "document_chunks",
        sa.Column(
            "provenance_state",
            sa.String(),
            server_default="LOW_PROVENANCE",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_document_chunks_revision_id",
        "document_chunks",
        "document_revisions",
        ["revision_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_document_chunks_revision_id", "document_chunks", ["revision_id"]
    )
    op.create_index(
        "ix_document_chunks_provenance_state", "document_chunks", ["provenance_state"]
    )

    _enable_tenant_rls("mesa_scope_bindings")
    _enable_tenant_rls("mesa_sync_records")


def downgrade() -> None:
    for table_name in ("mesa_sync_records", "mesa_scope_bindings"):
        op.execute(sa.text(f'ALTER TABLE "{table_name}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(f'DROP POLICY IF EXISTS tenant_isolation_policy ON "{table_name}"')
        )
        op.execute(sa.text(f'ALTER TABLE "{table_name}" DISABLE ROW LEVEL SECURITY'))

    op.drop_index("ix_document_chunks_provenance_state", table_name="document_chunks")
    op.drop_index("ix_document_chunks_revision_id", table_name="document_chunks")
    op.drop_constraint(
        "fk_document_chunks_revision_id", "document_chunks", type_="foreignkey"
    )
    for column in (
        "provenance_state",
        "extraction_version",
        "content_sha256",
        "character_end",
        "character_start",
        "revision_id",
    ):
        op.drop_column("document_chunks", column)

    op.drop_index(
        "ix_legal_assertions_publication_status", table_name="legal_assertions"
    )
    op.drop_index("ix_legal_assertions_canonical_status", table_name="legal_assertions")
    op.drop_index("ix_legal_assertions_assertion_type", table_name="legal_assertions")
    for column in (
        "publication_status",
        "canonical_status",
        "modality",
        "polarity",
        "object_data",
        "object_text",
        "predicate",
        "subject_text",
        "assertion_type",
    ):
        op.drop_column("legal_assertions", column)

    op.drop_index("ix_source_locators_provenance_state", table_name="source_locators")
    op.drop_index("ix_source_locators_chunk_id", table_name="source_locators")
    op.drop_constraint(
        "fk_source_locators_chunk_id", "source_locators", type_="foreignkey"
    )
    for column in (
        "verified_at",
        "provenance_state",
        "extraction_version",
        "evidence_sha256",
        "evidence_text",
        "chunk_id",
    ):
        op.drop_column("source_locators", column)

    op.drop_table("mesa_sync_records")
    op.drop_table("mesa_scope_bindings")
