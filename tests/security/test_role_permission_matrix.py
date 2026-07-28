import pytest
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.main import app
from fastapi import Request
from httpx import ASGITransport, AsyncClient

# Define the matrix
# Format: (Method, Endpoint, Allowed Roles)
MATRIX = [
    ("POST", "/api/v1/matters", {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}),
    ("POST", "/api/v1/matters/mat_123/rebuild-mesa", {"FIRM_ADMIN", "ATTORNEY"}),
    ("POST", "/api/v1/matters/mat_123/override-conflict", {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}),
    ("POST", "/api/v1/documents/upload-intent", {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}),
    ("POST", "/api/v1/draft-studio/drafts/draft_123/approve", {"FIRM_ADMIN", "ATTORNEY"}),
    ("PUT", "/api/v1/firms/firm_123/members/user_123/role", {"FIRM_ADMIN"}),
]

ROLES = ["FIRM_ADMIN", "ATTORNEY", "PARALEGAL", "READ_ONLY", "AUDITOR", "SUPPORT_TEMPORARY"]

@pytest.fixture
def override_context(monkeypatch):
    def _override(role: str):
        async def mock_setup(request: Request):
            return RequestContext(
                tenant_id="firm_123",
                principal_id="user_123",
                roles={role}
            )
        from apps.api.core.database import get_db
        from apps.api.dependencies.auth import require_recent_auth
        from unittest.mock import AsyncMock, MagicMock
        
        mock_session = AsyncMock()
        def mock_add(obj):
            setattr(obj, "id", "mock_id")
        mock_session.add = MagicMock(side_effect=mock_add)
        
        async def mock_refresh(obj):
            if not getattr(obj, "id", None):
                obj.id = "mock_id"
            if getattr(obj, "__tablename__", "") == "matters" and getattr(obj, "status", None) is None:
                obj.status = "OPEN"
                
        mock_session.refresh.side_effect = mock_refresh
        
        async def mock_get(model, obj_id):
            dummy = MagicMock()
            dummy.tenant_id = "firm_123"
            return dummy
            
        async def mock_execute(*args, **kwargs):
            dummy = MagicMock()
            member = MagicMock(tenant_id="firm_123", access_scope="admin")
            dummy.scalars.return_value.first.return_value = member
            return dummy
            
        mock_session.get.side_effect = mock_get
        mock_session.execute.side_effect = mock_execute
        
        app.dependency_overrides[setup_tenant_context] = mock_setup
        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[require_recent_auth] = lambda: True
        
        # Reset limiter to avoid 429
        from apps.api.core.ratelimit import limiter
        limiter._storage.reset()
    
    yield _override
    app.dependency_overrides.clear()

@pytest.mark.asyncio
@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("method,endpoint,allowed_roles", MATRIX)
async def test_rbac_matrix(override_context, role, method, endpoint, allowed_roles):
    override_context(role)
    
    # We use memory DB or rely on policies throwing 403 before DB is hit
    # For some policies, they need DB access (e.g. MatterAccessPolicy.can_read(context, matter_id)).
    # We might get 404 or 500 if DB is hit, but we MUST get 403 if RBAC blocks it.
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req_kwargs = {"headers": {"Authorization": "Bearer mock-e2e-token"}}
        if method in ["POST", "PUT"]:
            req_kwargs["json"] = {
                "dummy": "data", 
                "title": "test", 
                "jurisdiction": "TR", 
                "confidentiality_level": "standard", 
                "role": "ATTORNEY", 
                "reason": "test",
                "matter_id": "mat_123",
                "filename": "test.pdf",
                "size_bytes": 1024,
                "mime_type": "application/pdf"
            }
        
        res = await ac.request(method, endpoint, **req_kwargs)
        
    if role not in allowed_roles:
        assert res.status_code == 403, f"Expected 403 for {role} on {method} {endpoint}, got {res.status_code}"
    else:
        # If allowed, it shouldn't be 403 (might be 404/422/200 depending on mock DB)
        assert res.status_code != 403, f"Expected NOT 403 for {role} on {method} {endpoint}, got 403"
