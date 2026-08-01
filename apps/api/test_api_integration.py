from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apps.api.core.database import get_db
from apps.api.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_api_integration_e2e_flow():
    """
    Test the E2E integration flow:
    1. Create a Matter
    2. Request a document upload intent
    3. List matters to verify
    This test utilizes the mock-e2e-token to bypass Keycloak in test mode.
    """

    mock_session = AsyncMock()

    class MockMatter:
        id = "matter-123"
        title = "E2E Integration Matter"
        status = "open"

    class MockDoc:
        id = "doc-123"

    class MockRev:
        id = "rev-123"
        s3_key = "test/key"

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [MockMatter()]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_refresh(instance):
        pass

    def mock_add(instance):
        instance.id = f"mock-{instance.__class__.__name__.lower()}-123"
        instance.status = "open"

    mock_session.refresh = AsyncMock(side_effect=mock_refresh)
    mock_session.add = mock_add

    try:
        # Phase 6: Removed test_auth_enabled bypass, using actual jwt.decode mock
        with (
            patch("apps.api.dependencies.auth.jwt.decode") as mock_jwt_decode,
            patch("apps.api.dependencies.auth.get_jwks") as mock_get_jwks,
            patch(
                "apps.api.dependencies.auth.jwt.get_unverified_header"
            ) as mock_header,
            patch("apps.api.dependencies.auth.settings.env", "test"),
            patch(
                "apps.api.routers.documents.storage_service.generate_presigned_upload_url",
                new_callable=AsyncMock,
            ) as mock_presigned,
        ):
            mock_get_jwks.return_value = {"keys": [{"kid": "test-kid"}]}
            mock_header.return_value = {"kid": "test-kid"}
            mock_jwt_decode.return_value = {
                "sub": "test-user-id",
                "email": "test@example.com",
                "roles": [],
                "auth_time": 1700000000,
            }

            # Setup dependency override for tenant context
            from apps.api.core.models import RequestContext
            from apps.api.dependencies.auth import setup_tenant_context

            async def override_tenant_context():
                return RequestContext(
                    tenant_id="dev-tenant-default",
                    principal_id="test-user-id",
                    roles={"FIRM_ADMIN"},
                )

            app.dependency_overrides[setup_tenant_context] = override_tenant_context

            mock_presigned.return_value = "http://mock-presigned-url"

            headers = {
                "Authorization": "Bearer mock-e2e-token",
                "x-tenant-id": "dev-tenant-default",
            }

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # 1. Create a Matter
                # Note: DB is mocked, so we just check if endpoint handles request properly
                matter_resp = await client.post(
                    "/api/v1/matters",
                    json={"title": "E2E Integration Matter"},
                    headers=headers,
                )
                assert matter_resp.status_code == 201
                matter_data = matter_resp.json()
                assert "id" in matter_data
                matter_id = matter_data["id"]

                # 2. Upload Intent for a Document
                upload_resp = await client.post(
                    "/api/v1/documents/upload-intent",
                    json={
                        "filename": "e2e_test_doc.pdf",
                        "mime_type": "application/pdf",
                        "size_bytes": 1024,
                        "matter_id": matter_id,
                    },
                    headers=headers,
                )
                assert upload_resp.status_code == 200
                data = upload_resp.json()
                assert "document_id" in data
                assert "revision_id" in data
                assert "presigned_url" in data

                # 3. List Matters
                list_resp = await client.get("/api/v1/matters", headers=headers)
                assert list_resp.status_code == 200
                matters = list_resp.json()
                assert isinstance(matters, list)

    finally:
        app.dependency_overrides.clear()
