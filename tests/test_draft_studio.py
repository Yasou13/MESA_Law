import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from apps.api.main import app
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.core.models import RequestContext
from apps.api.core.database import get_db
from apps.api.models.draft import Draft

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
def override_draft_deps():
    mock_context = RequestContext(tenant_id="firm_123", principal_id="user-1", roles={"admin"})
    mock_session = AsyncMock()
    
    drafts_db = {}
    
    async def mock_get(model, obj_id):
        return drafts_db.get(obj_id)
        
    def mock_add(obj):
        if getattr(obj, "__tablename__", "") == "drafts":
            if not getattr(obj, "id", None):
                obj.id = "draft_123"
            drafts_db[obj.id] = obj
            
    async def mock_refresh(obj):
        if not getattr(obj, "id", None):
            obj.id = "draft_123"
            
    async def mock_execute(stmt):
        return MockResult(list(drafts_db.values()))
        
    mock_session.get.side_effect = mock_get
    mock_session.add = MagicMock(side_effect=mock_add)
    mock_session.refresh.side_effect = mock_refresh
    mock_session.execute.side_effect = mock_execute
    
    app.dependency_overrides[setup_tenant_context] = lambda: mock_context
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_draft_studio_crud_and_export(override_draft_deps):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create draft
        res = await ac.post(
            "/api/v1/draft-studio/drafts",
            json={"matter_id": "mat_123", "title": "Test Draft", "content": "Initial content"}
        )
        assert res.status_code == 200, res.text
        data = res.json()
        draft_id = data["id"]
        assert data["version"] == 1
        assert data["title"] == "Test Draft"

        # List drafts
        list_res = await ac.get("/api/v1/draft-studio/drafts/matter/mat_123")
        assert list_res.status_code == 200
        drafts = list_res.json()
        assert any(d["id"] == draft_id for d in drafts)

        # Get draft
        get_res = await ac.get(f"/api/v1/draft-studio/drafts/{draft_id}")
        assert get_res.status_code == 200
        assert get_res.json()["content"] == "Initial content"

        # Update draft
        put_res = await ac.put(
            f"/api/v1/draft-studio/drafts/{draft_id}",
            json={"title": "Updated Title", "content": "Updated content", "expected_version": 1}
        )
        assert put_res.status_code == 200
        put_data = put_res.json()
        assert put_data["version"] == 2
        assert put_data["title"] == "Updated Title"
        assert put_data["content"] == "Updated content"

        # Export draft
        exp_res = await ac.post(
            f"/api/v1/draft-studio/drafts/{draft_id}/export",
            json={"format": "pdf"}
        )
        assert exp_res.status_code == 200
        assert "job_id" in exp_res.json()
        assert exp_res.json()["version"] == 2
