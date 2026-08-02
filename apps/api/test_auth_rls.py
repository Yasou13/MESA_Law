import pytest
import uuid6
from apps.api.core.database import AsyncSessionLocal, get_db
from apps.api.core.errors import (
    ProblemException,
    global_exception_handler,
    problem_exception_handler,
)
from apps.api.core.rls import set_tenant_id
from apps.api.models.domain import Firm, Matter
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(ProblemException, problem_exception_handler)


@app.post("/test-matters")
async def create_matter(
    tenant_id: str = Header(...), db: AsyncSession = Depends(get_db)
):
    if not tenant_id:
        raise ProblemException(401, "Unauthorized", "Tenant missing")
    set_tenant_id(tenant_id)

    # Implicit RLS via loader criteria
    result = await db.execute(select(Matter))
    matters = result.scalars().all()
    return {"matters": [{"id": m.id, "title": m.title} for m in matters]}


@app.get("/test-matters-bypass")
async def fetch_matter_bypass(db: AsyncSession = Depends(get_db)):
    set_tenant_id(None)
    try:
        await db.execute(select(Matter))
    except Exception as e:
        if "RLS Guard" in str(e):
            return {"error": "blocked"}
        raise
    return {"error": "failed"}


client = TestClient(app)


@pytest.mark.asyncio
async def test_rls_guard_active():
    response = client.get("/test-matters-bypass")
    assert response.status_code == 200
    assert response.json() == {"error": "blocked"}


@pytest.mark.asyncio
async def test_tenant_isolation():
    tenant1_id = str(uuid6.uuid7())
    tenant2_id = str(uuid6.uuid7())

    async with AsyncSessionLocal() as db:
        # Avoid RLS errors when inserting by explicitly setting tenant
        set_tenant_id(tenant1_id)
        firm1 = Firm(id=tenant1_id, name="Tenant 1")
        firm2 = Firm(id=tenant2_id, name="Tenant 2")
        db.add(firm1)
        db.add(firm2)
        await db.flush()

        m1 = Matter(title="Matter 1", tenant_id=tenant1_id)
        db.add(m1)
        await db.flush()

        set_tenant_id(tenant2_id)
        m2 = Matter(title="Matter 2", tenant_id=tenant2_id)
        db.add(m2)
        await db.commit()

    # Query as tenant 1
    r1 = client.post("/test-matters", headers={"tenant-id": tenant1_id})
    assert r1.status_code == 200
    m_t1 = r1.json()["matters"]
    assert len(m_t1) == 1
    assert m_t1[0]["title"] == "Matter 1"

    # Query as tenant 2
    r2 = client.post("/test-matters", headers={"tenant-id": tenant2_id})
    m_t2 = r2.json()["matters"]
    assert len(m_t2) == 1
    assert m_t2[0]["title"] == "Matter 2"
