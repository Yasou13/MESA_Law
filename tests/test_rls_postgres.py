import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from apps.api.core.config import settings

@pytest.fixture(scope="module")
def postgres_url():
    # Attempt to connect to a real postgres if available
    return settings.effective_database_url

@pytest_asyncio.fixture(scope="module")
async def db_engine(postgres_url):
    engine = create_async_engine(postgres_url, echo=False)
    try:
        # Check connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        yield engine
    finally:
        await engine.dispose()

@pytest.mark.asyncio
async def test_real_postgres_rls_isolation(db_engine):
    """
    Test real PostgreSQL RLS by:
    1. Creating a table with RLS enabled
    2. Inserting data for Tenant A and Tenant B
    3. Setting app.current_tenant to Tenant A
    4. Asserting that only Tenant A's data is visible.
    """
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with db_engine.begin() as conn:
        # Create a temp table with RLS
        await conn.execute(text("""
            CREATE TEMP TABLE test_rls_table (
                id serial PRIMARY KEY,
                tenant_id varchar NOT NULL,
                data varchar NOT NULL
            );
        """))
        await conn.execute(text("ALTER TABLE test_rls_table ENABLE ROW LEVEL SECURITY;"))
        await conn.execute(text("""
            CREATE POLICY tenant_isolation_policy ON test_rls_table
            FOR ALL
            USING (tenant_id = current_setting('app.current_tenant', true));
        """))
        
        # Insert data as superuser (RLS bypasses normally for table owner, 
        # but since we want to test policies, we must ensure we use SET ROLE if needed.
        # But wait, default postgres user is superuser, which bypasses RLS.
        # So we force enable RLS for the table owner.
        await conn.execute(text("ALTER TABLE test_rls_table FORCE ROW LEVEL SECURITY;"))
        
        # Bypass RLS to insert data
        await conn.execute(text("SELECT set_config('app.current_tenant', 'tenant_A', false)"))
        await conn.execute(text("INSERT INTO test_rls_table (tenant_id, data) VALUES ('tenant_A', 'A_data')"))
        
        await conn.execute(text("SELECT set_config('app.current_tenant', 'tenant_B', false)"))
        await conn.execute(text("INSERT INTO test_rls_table (tenant_id, data) VALUES ('tenant_B', 'B_data')"))
        
    async with async_session() as session:
        # Set tenant A context
        await session.execute(text("SELECT set_config('app.current_tenant', 'tenant_A', false)"))
        
        # Query data
        result = await session.execute(text("SELECT data FROM test_rls_table"))
        rows = result.scalars().all()
        
        assert len(rows) == 1
        assert rows[0] == 'A_data'
        
        # Switch to Tenant B
        await session.execute(text("SELECT set_config('app.current_tenant', 'tenant_B', false)"))
        
        result2 = await session.execute(text("SELECT data FROM test_rls_table"))
        rows2 = result2.scalars().all()
        
        assert len(rows2) == 1
        assert rows2[0] == 'B_data'
        
    async with db_engine.begin() as conn:
        await conn.execute(text("DROP TABLE test_rls_table"))
