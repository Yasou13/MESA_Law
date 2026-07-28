import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from fastapi import Request

# Mock setup_tenant_context to represent Tenant A
@pytest.fixture
def override_tenant_a():
    async def mock_setup(request: Request):
        return RequestContext(
            tenant_id="tenant_A",
            principal_id="user_A",
            roles={"FIRM_ADMIN"}
        )
    app.dependency_overrides[setup_tenant_context] = mock_setup
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_cross_tenant_matter_access(override_tenant_a, monkeypatch):
    # Try to access matter belonging to Tenant B
    from apps.api.models.domain import Matter
    
    # We monkeypatch the SQLAlchemy session.get or execute to return a Matter belonging to tenant_B
    async def mock_get(*args, **kwargs):
        m = Matter(title="Tenant B Matter", tenant_id="tenant_B", jurisdiction="TR", confidentiality_level="standard")
        m.id = "mat_tenant_B"
        return m
        
    monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession.get", mock_get)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Actually our routers check `matter.tenant_id == context.tenant_id`
        res = await ac.get("/api/v1/matters/mat_tenant_B", headers={"Authorization": "Bearer mock-e2e-token"})
        
    # We might get 404 (due to RLS or router hiding it) or 403.
    # The requirement is cross-tenant leakage = 0. So it shouldn't return 200.
    assert res.status_code in [403, 404], f"Cross-tenant matter access should be blocked, got {res.status_code}"

@pytest.mark.asyncio
async def test_cross_tenant_draft_access(override_tenant_a, monkeypatch):
    from apps.api.models.draft import Draft
    
    async def mock_get(*args, **kwargs):
        d = Draft(tenant_id="tenant_B", matter_id="mat_B", title="Draft B", content="content", version=1)
        d.id = "draft_tenant_B"
        return d
        
    monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession.get", mock_get)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/draft-studio/drafts/draft_tenant_B", headers={"Authorization": "Bearer mock-e2e-token"})
        
    assert res.status_code in [403, 404], f"Cross-tenant draft access should be blocked, got {res.status_code}"

@pytest.mark.asyncio
async def test_cross_tenant_document_download(override_tenant_a, monkeypatch):
    from apps.api.models.document import Document
    
    async def mock_get(*args, **kwargs):
        d = Document(tenant_id="tenant_B", matter_id="mat_B", filename="test.pdf", s3_key="tenant_B/test.pdf", size_bytes=100)
        d.id = "doc_tenant_B"
        return d
        
    monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession.get", mock_get)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/documents/doc_tenant_B/download", headers={"Authorization": "Bearer mock-e2e-token"})
        
    assert res.status_code in [403, 404], f"Cross-tenant document download should be blocked, got {res.status_code}"
