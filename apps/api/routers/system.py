import asyncio
from urllib.parse import urlparse

import httpx
from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import AdminAccessPolicy
from apps.api.dependencies.auth import require_recent_auth, setup_tenant_context
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["System"])


class FeatureSettings(BaseModel):
    mesa_rebuild_enabled: bool
    external_research_enabled: bool
    document_ocr_enabled: bool
    drafting_ai_enabled: bool
    deadline_ai_enabled: bool


class RetentionSettings(BaseModel):
    audit_log_days: int
    deleted_document_days: int


class SecuritySettings(BaseModel):
    require_mfa: bool
    session_timeout_minutes: int


class SystemSettingsResponse(BaseModel):
    features: FeatureSettings
    retention: RetentionSettings
    security: SecuritySettings


class HealthResponse(BaseModel):
    status: str
    components: dict[str, str]


async def check_tcp(host: str, port: int, timeout: float | None = None) -> bool:
    effective_timeout = timeout or settings.health_timeout_seconds
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=effective_timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, TimeoutError):
        return False


async def check_http(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> bool:
    try:
        async with httpx.AsyncClient(
            timeout=timeout or settings.health_timeout_seconds,
            follow_redirects=False,
        ) as client:
            response = await client.get(url, headers=headers)
        return 200 <= response.status_code < 400
    except httpx.HTTPError:
        return False


def _host_and_port(url: str, default_port: int) -> tuple[str, int]:
    parsed = urlparse(url)
    return parsed.hostname or "localhost", parsed.port or default_port


def _keycloak_discovery_url() -> str:
    issuer_path = urlparse(settings.keycloak_issuer).path.rstrip("/")
    base_url = settings.keycloak_internal_url or settings.keycloak_issuer
    if settings.keycloak_internal_url:
        base_url = f"{base_url.rstrip('/')}{issuer_path}"
    return f"{base_url.rstrip('/')}/.well-known/openid-configuration"


@router.get("/health/live", response_model=HealthResponse, operation_id="liveProbe")
async def live() -> HealthResponse:
    return HealthResponse(status="ok", components={"process": "ok"})


@router.get("/health/ready", response_model=HealthResponse, operation_id="readyProbe")
async def ready(
    response: Response, db: AsyncSession = Depends(get_db)
) -> HealthResponse:
    dependencies = await get_dependencies(db)
    required = {"postgres", "redis", "object_storage", "keycloak"}
    if settings.clamav_required:
        required.add("clamav")
    if any(dependencies[name] != "ok" for name in required):
        response.status_code = 503
        return HealthResponse(status="unavailable", components=dependencies)
    degraded = any(
        value not in {"ok", "disabled", "mock"}
        for name, value in dependencies.items()
        if name not in required
    )
    return HealthResponse(
        status="degraded" if degraded else "ok",
        components=dependencies,
    )


@router.get(
    "/api/v1/system/dependencies",
    response_model=dict[str, str],
    operation_id="getSystemDependencies",
)
async def system_dependencies(
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    AdminAccessPolicy.can_manage_firm(context)
    return await get_dependencies(db)


@router.get(
    "/api/v1/system/settings",
    operation_id="getSystemSettings",
    response_model=SystemSettingsResponse,
)
async def get_system_settings(
    context: RequestContext = Depends(setup_tenant_context),
):
    return {
        "features": {
            "mesa_rebuild_enabled": settings.mesa_rebuild_enabled,
            "external_research_enabled": settings.external_research_enabled,
            "document_ocr_enabled": True,
            "drafting_ai_enabled": settings.drafting_ai_enabled,
            "deadline_ai_enabled": settings.deadline_ai_enabled,
        },
        "retention": {"audit_log_days": 90, "deleted_document_days": 30},
        "security": {"require_mfa": True, "session_timeout_minutes": 60},
    }


@router.put("/api/v1/system/settings", operation_id="updateSystemSettings")
async def update_system_settings(
    payload: SystemSettingsResponse,
    context: RequestContext = Depends(setup_tenant_context),
):
    AdminAccessPolicy.can_manage_firm(context)
    raise HTTPException(
        status_code=501,
        detail="Runtime settings mutation is not available in the MVP",
    )


@router.post("/api/v1/system/sync-mesa-core", operation_id="syncMesaCore")
async def sync_mesa_core(
    context: RequestContext = Depends(setup_tenant_context),
    _recent_auth: None = Depends(require_recent_auth),
):
    AdminAccessPolicy.can_manage_firm(context)
    raise HTTPException(
        status_code=501,
        detail="MESA Core pull-sync is not part of the MVP contract",
    )


async def get_dependencies(db: AsyncSession) -> dict[str, str]:
    dependencies = {
        "postgres": "down",
        "object_storage": "down",
        "redis": "down",
        "keycloak": "down",
        "clamav": "down",
        "intelligence_adapter": "degraded",
    }

    try:
        await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=settings.health_timeout_seconds,
        )
        dependencies["postgres"] = "ok"
    except (SQLAlchemyError, TimeoutError):
        pass

    redis_host, redis_port = _host_and_port(settings.redis_url, 6379)
    storage_host, storage_port = _host_and_port(settings.storage_endpoint, 9000)
    storage_url = f"{settings.storage_endpoint.rstrip('/')}/minio/health/ready"
    mesa_headers = (
        {"X-API-Key": settings.mesa_api_key} if settings.mesa_api_key else None
    )
    checks = await asyncio.gather(
        check_tcp(redis_host, redis_port),
        check_http(_keycloak_discovery_url()),
        check_tcp(settings.clamav_host, settings.clamav_port),
        check_tcp(storage_host, storage_port),
        check_http(storage_url),
    )
    redis_ok, keycloak_ok, clamav_ok, storage_tcp_ok, storage_http_ok = checks
    dependencies["redis"] = "ok" if redis_ok else "down"
    dependencies["keycloak"] = "ok" if keycloak_ok else "down"
    dependencies["clamav"] = (
        "ok" if clamav_ok else "down" if settings.clamav_required else "disabled"
    )
    dependencies["object_storage"] = (
        "ok" if storage_tcp_ok and storage_http_ok else "down"
    )

    adapter = settings.intelligence_adapter.lower()
    if adapter == "mock":
        dependencies["intelligence_adapter"] = "mock"
    elif adapter != "mesa_v4" or not settings.mesa_api_key:
        dependencies["intelligence_adapter"] = "unconfigured"
    else:
        mesa_ok = await check_http(
            f"{settings.mesa_backend_url.rstrip('/')}/v4/capability",
            headers=mesa_headers,
        )
        dependencies["intelligence_adapter"] = "ok" if mesa_ok else "down"
    return dependencies
