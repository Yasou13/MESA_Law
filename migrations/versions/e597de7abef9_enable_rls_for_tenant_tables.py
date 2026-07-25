"""enable_rls_for_tenant_tables

Revision ID: e597de7abef9
Revises: b32fcdcbcf80
Create Date: 2026-07-25 21:53:35.281230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e597de7abef9'
down_revision: Union[str, Sequence[str], None] = 'b32fcdcbcf80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_tables = [
        "matters",
        "documents",
        "parsed_documents",
        "legal_review_queue",
        "legal_audit_logs",
        
    ]
    
    for table in tenant_tables:
        # Enable RLS on the table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        
        # Create policy based on current_setting
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            AS PERMISSIVE
            FOR ALL
            TO PUBLIC
            USING (tenant_id = current_setting('app.current_tenant', true)::text)
            WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::text);
        """)
        
        # Force RLS for table owner as well, just to be safe
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    tenant_tables = [
        "matters",
        "documents",
        "parsed_documents",
        "legal_review_queue",
        "legal_audit_logs",
        
    ]
    
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
