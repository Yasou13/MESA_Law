import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from apps.api.models.domain import Matter
from apps.api.core.rls import set_tenant_id

@pytest.mark.asyncio
async def test_tenant_rls_isolation():
    # Setup test DB using superuser to bypass RLS for seeding
    su_url = "postgresql+psycopg://mesa:mesa@127.0.0.1:5432/mesa_law"
    su_engine = create_async_engine(su_url)
    su_session = async_sessionmaker(su_engine, expire_on_commit=False)()
    
    from apps.api.models.domain import Firm
    import uuid
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    
    firm_a = Firm(id=tenant_a, name="Firm A")
    firm_b = Firm(id=tenant_b, name="Firm B")
    su_session.add_all([firm_a, firm_b])
    await su_session.commit()
    
    matter_a = Matter(title="Matter A", tenant_id=tenant_a)
    matter_b = Matter(title="Matter B", tenant_id=tenant_b)
    
    su_session.add_all([matter_a, matter_b])
    await su_session.commit()
    await su_session.close()
    
    # Query as mesa_law_app with NOBYPASSRLS
    url = "postgresql+psycopg://mesa_law_app:app_pass@127.0.0.1:5432/mesa_law"
    engine = create_async_engine(url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Start transaction for Tenant A
        set_tenant_id(tenant_a)
        
        from sqlalchemy import select
        # ORM query (which adds where clause)
        res = await session.execute(select(Matter))
        matters = res.scalars().all()
        assert len(matters) == 1, "App-level RLS failed"
        assert matters[0].title == "Matter A"
        
        # Raw query to test DB-level RLS explicitly bypassing App-level filter
        # It should ONLY return Tenant A's matters because set_config was run
        res = await session.execute(text("SELECT id, title, tenant_id FROM matters"))
        raw_matters = res.all()
        
        assert len(raw_matters) == 1, "DB-level RLS failed! Returned matters outside tenant."
        assert raw_matters[0].tenant_id == tenant_a
        
        await session.commit()
        
    async with SessionLocal() as session:
        # Start transaction for Tenant B
        set_tenant_id(tenant_b)
        
        res = await session.execute(text("SELECT id, title, tenant_id FROM matters"))
        raw_matters_b = res.all()
        assert len(raw_matters_b) == 1
        assert raw_matters_b[0].tenant_id == tenant_b
