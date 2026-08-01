import pytest
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.main import app
from fastapi import Request
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def override_tenant():
    async def mock_setup(request: Request):
        return RequestContext(
            tenant_id="tenant_A", principal_id="user_A", roles={"FIRM_ADMIN"}
        )

    from unittest.mock import AsyncMock

    from apps.api.core.database import get_db

    mock_db = AsyncMock()

    class MockResult:
        def __init__(self, data):
            self.data = data

        def all(self):
            return self.data

        def scalars(self):
            class _Scalars:
                def all(self):
                    return []

                def first(self):
                    return type("Member", (), {"access_scope": "admin"})()

            return _Scalars()

    mock_db.execute = AsyncMock(return_value=MockResult([]))
    app.dependency_overrides[setup_tenant_context] = mock_setup
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_degraded_mode_llm_failure(override_tenant, monkeypatch):
    # Simulate LLM completely failing / timeout
    import apps.api.routers.qa

    async def mock_ask(*args, **kwargs):
        raise TimeoutError("LLM Provider Unreachable")

    monkeypatch.setattr(apps.api.routers.qa, "ask_matter_question", mock_ask)

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as ac:
        res_llm = await ac.post(
            "/api/v1/qa/ask",
            json={"matter_id": "mat_123", "question": "test"},
            headers={"Authorization": "Bearer mock"},
        )
        assert res_llm.status_code == 500

        # Manual matter management
        res_manual = await ac.get(
            "/api/v1/matters", headers={"Authorization": "Bearer mock"}
        )

    # The application itself hasn't crashed. Matters endpoint still works.
    assert res_manual.status_code == 200
