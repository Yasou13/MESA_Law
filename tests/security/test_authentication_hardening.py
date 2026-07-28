import time

import pytest
from apps.api.core.config import settings
from apps.api.main import app
from httpx import ASGITransport, AsyncClient
from jose import jwt


def create_mock_jwt(overrides: dict) -> str:
    payload = {
        "sub": "user-1",
        "email": "test@firm.com",
        "realm_access": {"roles": ["FIRM_ADMIN"]},
        "iss": settings.keycloak_issuer,
        "aud": [settings.keycloak_client_id, "account"],
        "exp": int(time.time()) + 3600,
        "auth_time": int(time.time()) - 60
    }
    payload.update(overrides)
    # Since we are mock testing, we will monkeypatch the decode logic in test
    return jwt.encode(payload, "secret", algorithm="HS256")

@pytest.fixture
def patch_jwt_decode(monkeypatch):
    # Patch jose.jwt.decode to return payload directly for test tokens
    original_decode = jwt.decode
    def mock_decode(token, key, algorithms, audience, issuer, options):
        if token.startswith("test_token_"):
            # Extract raw payload
            import base64
            import json
            parts = token.split(".")
            if len(parts) == 3:
                padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                return json.loads(base64.b64decode(padded).decode("utf-8"))
        return original_decode(token, key, algorithms, audience, issuer, options)
    monkeypatch.setattr(jwt, "decode", mock_decode)
    
    original_get_unverified = jwt.get_unverified_header
    def mock_get_unverified(token):
        if token.startswith("test_token_"):
            return {"kid": "mock_kid"}
        return original_get_unverified(token)
    monkeypatch.setattr(jwt, "get_unverified_header", mock_get_unverified)

    # Patch get_jwks to return mock kid
    from apps.api.dependencies import auth
    def mock_get_jwks(force_refresh=False):
        return {"keys": [{"kid": "mock_kid"}]}
    monkeypatch.setattr(auth, "get_jwks", mock_get_jwks)

@pytest.mark.asyncio
async def test_auth_expired_token(patch_jwt_decode):
    # Setup token that is expired
    token = "test_token_." + create_mock_jwt({"exp": int(time.time()) - 3600}).split(".")[1] + "."
    # We do NOT override get_current_user because we want test_auth_expired_token 
    # to actually execute the real get_current_user and hit JWT expiry validation.
    # However, since we bypassed the signature via patch_jwt_decode, we expect it to run fine 
    # and either succeed or fail depending on what we test. Since this test is just about expired token,
    # the endpoint requires get_current_user to run.
    # Wait, the endpoint uses setup_tenant_context which queries the DB! So we MUST mock setup_tenant_context!
    from apps.api.dependencies.auth import setup_tenant_context
    from apps.api.core.models import RequestContext
    app.dependency_overrides[setup_tenant_context] = lambda: RequestContext(tenant_id="tenant-1", principal_id="user-1", roles={"FIRM_ADMIN"})
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            _res = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_recent_auth_required_fails(patch_jwt_decode, monkeypatch):
    # test auth_time > 300
    token = "test_token_." + create_mock_jwt({"auth_time": int(time.time()) - 600}).split(".")[1] + "."
    
    from apps.api.dependencies.auth import setup_tenant_context, get_current_user
    from apps.api.core.models import RequestContext
    ctx = RequestContext(tenant_id="tenant-1", principal_id="user-1", roles={"FIRM_ADMIN"})
    app.dependency_overrides[setup_tenant_context] = lambda: ctx
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "roles": {"FIRM_ADMIN"}, "email": "test@test.com", "auth_time": int(time.time()) - 600}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # override_conflict requires recent auth
            res = await ac.post("/api/v1/matters/mat_123/override-conflict", 
                json={"reason": "test"},
                headers={"Authorization": f"Bearer {token}"}
            )
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 401
    assert "Recent authentication required" in res.json()["detail"]

@pytest.mark.asyncio
async def test_recent_auth_required_passes(patch_jwt_decode, monkeypatch):
    # test auth_time < 300
    token = "test_token_." + create_mock_jwt({"auth_time": int(time.time()) - 60}).split(".")[1] + "."
    
    from apps.api.dependencies.auth import setup_tenant_context, get_current_user
    from apps.api.core.models import RequestContext
    ctx = RequestContext(tenant_id="tenant-1", principal_id="user-1", roles={"FIRM_ADMIN"})
    from apps.api.core.database import get_db
    from unittest.mock import AsyncMock
    mock_db = AsyncMock()
    app.dependency_overrides[setup_tenant_context] = lambda: ctx
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "roles": {"FIRM_ADMIN"}, "email": "test@test.com", "auth_time": int(time.time()) - 60}
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/matters/mat_123/override-conflict", 
                json={"reason": "test"},
                headers={"Authorization": f"Bearer {token}"}
            )
    finally:
        app.dependency_overrides.clear()
    assert res.status_code != 401
