import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from fastapi import Request

# Define the matrix
# Format: (Method, Endpoint, Allowed Roles)
MATRIX = [
    ("POST", "/api/v1/matters", {"FIRM_ADMIN", "ATTORNEY"}),
    ("POST", "/api/v1/matters/mat_123/rebuild-mesa", {"FIRM_ADMIN"}),
    ("POST", "/api/v1/matters/mat_123/override-conflict", {"FIRM_ADMIN", "ATTORNEY"}),
    ("POST", "/api/v1/documents", {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}),
    ("POST", "/api/v1/draft-studio/drafts/draft_123/approve", {"FIRM_ADMIN", "ATTORNEY"}),
    ("PUT", "/api/v1/firms/firm_123/members/user_123/role", {"FIRM_ADMIN"}),
]

ROLES = ["FIRM_ADMIN", "ATTORNEY", "PARALEGAL", "READ_ONLY", "AUDITOR", "SUPPORT_TEMPORARY"]

@pytest.fixture
def override_context(monkeypatch):
    def _override(role: str):
        async def mock_setup(request: Request):
            return RequestContext(
                tenant_id="tenant_123",
                principal_id="user_123",
                roles={role}
            )
        app.dependency_overrides[setup_tenant_context] = mock_setup
    
    yield _override
    app.dependency_overrides = {}

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
            req_kwargs["json"] = {"dummy": "data", "title": "test", "jurisdiction": "TR", "confidentiality_level": "standard", "role": "ATTORNEY", "reason": "test"}
        
        res = await ac.request(method, endpoint, **req_kwargs)
        
    if role not in allowed_roles:
        assert res.status_code == 403, f"Expected 403 for {role} on {method} {endpoint}, got {res.status_code}"
    else:
        # If allowed, it shouldn't be 403 (might be 404/422/200 depending on mock DB)
        assert res.status_code != 403, f"Expected NOT 403 for {role} on {method} {endpoint}, got 403"
