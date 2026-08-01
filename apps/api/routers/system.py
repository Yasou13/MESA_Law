import asyncio
import os
import socket

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


async def check_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        connection = await asyncio.to_thread(
            socket.create_connection, (host, port), timeout
        )
        connection.close()
        return True
    except OSError:
        return False


@router.get("/health/live")
async def live():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(response: Response, db: AsyncSession = Depends(get_db)):
    dependencies = await get_dependencies(db)
    if dependencies["postgres"] != "ok":
        response.status_code = 503
        return {"status": "unavailable", "components": dependencies}
    return {"status": "ok", "components": dependencies}


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
        await db.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except SQLAlchemyError:  # Dependency health must report failure instead of raising.
        pass

    checks = await asyncio.gather(
        check_tcp("redis", 6379),
        check_tcp("keycloak", 8080),
        check_tcp("clamav", 3310),
        check_tcp("minio", 9000),
    )
    for name, available in zip(
        ("redis", "keycloak", "clamav", "object_storage"), checks, strict=True
    ):
        if available:
            dependencies[name] = "ok"

    adapter = os.getenv("MESA_LAW_INTELLIGENCE_ADAPTER", "mock").lower()
    dependencies["intelligence_adapter"] = "mock" if adapter == "mock" else "degraded"
    return dependencies
