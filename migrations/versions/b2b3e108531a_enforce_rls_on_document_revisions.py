"""Enforce RLS on document_revisions

Revision ID: b2b3e108531a
Revises: f5d27f07a1d3
Create Date: 2026-07-27 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2b3e108531a'
down_revision: Union[str, Sequence[str], None] = 'f5d27f07a1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    table = "document_revisions"
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
    table = "document_revisions"
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
