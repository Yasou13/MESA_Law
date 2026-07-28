import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from apps.api.main import app
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.core.models import RequestContext
from apps.api.core.database import get_db

class MockResult:
    def __init__(self, items=None):
        self.items = items or []
    def scalars(self):
        return self
    def all(self):
        return self.items
    def first(self):
        return self.items[0] if self.items else None
    def __iter__(self):
        return iter(self.items)

@pytest.fixture
def mock_context():
    return RequestContext(tenant_id="e2e-tenant-123", principal_id="user-1", roles={"admin"})

@pytest.fixture
def override_deps(mock_context):
    mock_session = AsyncMock()
    mock_session.execute.return_value = MockResult([])
    app.dependency_overrides[setup_tenant_context] = lambda: mock_context
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_timeline_endpoint(override_deps):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/matters/matter-1/timeline")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_claims_evidence_endpoint(override_deps):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/matters/matter-1/claims-evidence")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_research_search_endpoint(override_deps):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/research/search?q=borçlar")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_qa_ask_endpoint_fallback(override_deps):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/ask", json={"matter_id": "matter-1", "question": "Kıdem tazminatı şartları nelerdir?"})
    assert res.status_code == 200
    data = res.json()
    assert "[test mock]" in data["answer"].lower()
    assert len(data["citations"]) == 0

