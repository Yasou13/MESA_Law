import time

import pytest
from apps.api.core.config import settings
from apps.api.dependencies.auth import get_current_user, require_recent_auth
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import ExpiredSignatureError


def create_mock_jwt(overrides: dict) -> str:
    payload = {
        "sub": "user-1",
        "email": "test@firm.com",
        "realm_access": {"roles": ["FIRM_ADMIN"]},
        "iss": settings.keycloak_issuer,
        "aud": [settings.keycloak_client_id, "account"],
        "exp": int(time.time()) + 3600,
        "auth_time": int(time.time()) - 60,
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
                payload = json.loads(base64.b64decode(padded).decode("utf-8"))
                if payload.get("exp", 0) < time.time():
                    raise ExpiredSignatureError("Signature has expired")
                return payload
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

    async def inline_to_thread(function, *args):
        return function(*args)

    monkeypatch.setattr(auth, "get_jwks", mock_get_jwks)
    monkeypatch.setattr(auth.asyncio, "to_thread", inline_to_thread)


@pytest.mark.asyncio
async def test_auth_expired_token(patch_jwt_decode):
    token = (
        "test_token_."
        + create_mock_jwt({"exp": int(time.time()) - 3600}).split(".")[1]
        + "."
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as raised:
        await get_current_user(credentials)
    assert raised.value.status_code == 401
    assert raised.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_recent_auth_required_fails(patch_jwt_decode):
    token = (
        "test_token_."
        + create_mock_jwt({"auth_time": int(time.time()) - 600}).split(".")[1]
        + "."
    )
    request = Request(
        {"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]}
    )
    with pytest.raises(HTTPException) as raised:
        await require_recent_auth(request)
    assert raised.value.status_code == 401
    assert raised.value.detail == "Recent authentication required"


@pytest.mark.asyncio
async def test_recent_auth_required_passes(patch_jwt_decode):
    token = (
        "test_token_."
        + create_mock_jwt({"auth_time": int(time.time()) - 60}).split(".")[1]
        + "."
    )
    request = Request(
        {"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]}
    )
    await require_recent_auth(request)
