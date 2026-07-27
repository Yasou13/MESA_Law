"""Enforce RLS on all tenant tables and create app role

Revision ID: 39e9a5e1a894
Revises: f1a2b3c4d5e6
Create Date: 2026-07-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39e9a5e1a894'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create mesa_law_app role if not exists
    op.execute("""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mesa_law_app') THEN
            CREATE ROLE mesa_law_app NOLOGIN;
          END IF;
        END
        $$;
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mesa_law_app;")

    # 2. Apply RLS on missing tables that were explicitly mentioned in Phase 3
    remaining_tables = [
        "matter_events",
        "defenses",
        "claim_evidence_links",
        "review_items",
        "draft_revisions",
        "draft_citations",
        "operations",
        "jobs"
    ]
    
    for table in remaining_tables:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table}') THEN
                    EXECUTE 'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY';
                    EXECUTE 'DROP POLICY IF EXISTS tenant_isolation_policy ON {table}';
                    EXECUTE 'CREATE POLICY tenant_isolation_policy ON {table} AS PERMISSIVE FOR ALL TO PUBLIC USING (tenant_id = current_setting(''app.current_tenant'', true)::text) WITH CHECK (tenant_id = current_setting(''app.current_tenant'', true)::text)';
                    EXECUTE 'ALTER TABLE {table} FORCE ROW LEVEL SECURITY';
                END IF;
            END
            $$;
        """)

def downgrade() -> None:
    remaining_tables = [
        "matter_events",
        "defenses",
        "claim_evidence_links",
        "review_items",
        "draft_revisions",
        "draft_citations",
        "operations",
        "jobs"
    ]
    
    for table in remaining_tables:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table}') THEN
                    EXECUTE 'ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY';
                    EXECUTE 'DROP POLICY IF EXISTS tenant_isolation_policy ON {table}';
                    EXECUTE 'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY';
                END IF;
            END
            $$;
        """)
