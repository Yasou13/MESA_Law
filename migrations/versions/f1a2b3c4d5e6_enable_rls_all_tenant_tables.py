"""enable_rls_all_tenant_tables

Revision ID: f1a2b3c4d5e6
Revises: 97a1b2c3d4e5
Create Date: 2026-07-25 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '97a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_tables = [
        "matter_parties",
        "claims",
        "evidence_items",
        "legal_assertions",
        "drafts",
        "deadline_rules",
        "potential_deadlines",
        "approved_deadlines",
        "audit_events",
        "notifications"
    ]
    
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            AS PERMISSIVE
            FOR ALL
            TO PUBLIC
            USING (tenant_id = current_setting('app.current_tenant', true)::text)
            WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::text);
        """)
        
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    tenant_tables = [
        "matter_parties",
        "claims",
        "evidence_items",
        "legal_assertions",
        "drafts",
        "deadline_rules",
        "potential_deadlines",
        "approved_deadlines",
        "audit_events",
        "notifications"
    ]
    
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
