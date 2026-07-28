from unittest.mock import AsyncMock, patch

import pytest
from apps.api.core.database import get_db
from apps.api.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_live_probe():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health/live")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_health_ready_probe_success():
    mock_session = AsyncMock()
    mock_session.execute.return_value = None
    
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("apps.api.routers.system.check_tcp", new_callable=AsyncMock) as mock_tcp:
            mock_tcp.return_value = True
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.get("/health/ready")
                assert res.status_code == 200
                data = res.json()
                assert data["status"] == "ok"
                assert data["components"]["postgres"] == "ok"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_health_ready_probe_failure_when_db_down():
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("DB Connection Refused")
    
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/health/ready")
            assert res.status_code == 503
            data = res.json()
            assert data["status"] == "unavailable"
            assert data["components"]["postgres"] == "down"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_system_dependencies_probe():
    mock_session = AsyncMock()
    mock_session.execute.return_value = None
    
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("apps.api.routers.system.check_tcp", new_callable=AsyncMock) as mock_tcp:
            mock_tcp.return_value = True
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.get("/api/v1/system/dependencies")
                assert res.status_code == 200
                deps = res.json()
                assert deps["postgres"] == "ok"
                assert deps["redis"] == "ok"
                assert deps["object_storage"] == "ok"
    finally:
        app.dependency_overrides.clear()
