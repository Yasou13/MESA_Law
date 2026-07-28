import os
import socket

from apps.api.core.database import get_db
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context, require_recent_auth
from apps.api.core.policies import AdminAccessPolicy

router = APIRouter(tags=["System"])

async def check_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        conn = socket.create_connection((host, port), timeout=timeout)
        conn.close()
        return True
    except Exception:
        return False

@router.get("/health/live")
async def live():
    return {"status": "ok"}

@router.get("/health/ready")
async def ready(response: Response, db: AsyncSession = Depends(get_db)):
    deps = await get_dependencies(db)
    # API is ready if Postgres is up
    is_ready = deps["postgres"] == "ok"
    if not is_ready:
        response.status_code = 503
        return {"status": "unavailable", "components": deps}
    
    return {"status": "ok", "components": deps}

@router.get("/api/v1/system/dependencies")
async def system_dependencies(
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    AdminAccessPolicy.can_admin_firm(context)
    return await get_dependencies(db)

@router.get("/api/v1/system/settings", operation_id="getSystemSettings")
async def get_system_settings(
    context: RequestContext = Depends(setup_tenant_context)
):
    # Any authenticated user can read settings (auth enforced by setup_tenant_context)
    return {
        "features": {
            "advanced_search_enabled": True,
            "document_ocr_enabled": True,
            "drafting_ai_enabled": True
        },
        "retention": {
            "audit_log_days": 90,
            "deleted_document_days": 30
        },
        "security": {
            "require_mfa": False,
            "session_timeout_minutes": 60
        }
    }

@router.put("/api/v1/system/settings", operation_id="updateSystemSettings")
async def update_system_settings(
    payload: dict,
    context: RequestContext = Depends(setup_tenant_context)
):
    AdminAccessPolicy.can_admin_firm(context)
    # Mock update endpoint
    return {"status": "success", "settings": payload}

from pydantic import BaseModel


class SyncMesaCoreRequest(BaseModel):
    tenant_id: str

@router.post("/api/v1/system/sync-mesa-core", operation_id="syncMesaCore")
async def sync_mesa_core(
    payload: SyncMesaCoreRequest,
    db: AsyncSession = Depends(get_db)
):
    import logging
    import uuid

    from apps.api.models.document import Document
    logger = logging.getLogger(__name__)

    # Create dummy document to simulate sync from MESA Core
    dummy_doc = Document(
        tenant_id=payload.tenant_id,
        filename="MESA_Core_Sync_Sample.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        status="PROCESSED",
        object_key=f"mesa-core-sync/{uuid.uuid4()}.pdf"
    )
    db.add(dummy_doc)
    await db.commit()
    await db.refresh(dummy_doc)

    logger.info(f"Synced from MESA Core: Document {dummy_doc.id}")

    return {
        "status": "success",
        "message": "Synced from MESA Core",
        "document_id": dummy_doc.id
    }

async def get_dependencies(db: AsyncSession) -> dict:
    deps = {
        "postgres": "down",
        "object_storage": "down",
        "redis": "down",
        "keycloak": "down",
        "clamav": "down",
        "intelligence_adapter": "degraded"
    }

    # Postgres
    try:
        await db.execute(text("SELECT 1"))
        deps["postgres"] = "ok"
    except Exception:
        pass

    # Redis
    if await check_tcp("redis", 6379):
        deps["redis"] = "ok"
        
    # Keycloak
    if await check_tcp("keycloak", 8080):
        deps["keycloak"] = "ok"
        
    # ClamAV
    if await check_tcp("clamav", 3310):
        deps["clamav"] = "ok"

    # MinIO
    if await check_tcp("minio", 9000):
        deps["object_storage"] = "ok"

    # Intelligence Adapter
    adapter = os.getenv("MESA_LAW_INTELLIGENCE_ADAPTER", "mock").lower()
    if adapter == "mock":
        deps["intelligence_adapter"] = "mock"
    else:
        deps["intelligence_adapter"] = "degraded"

    return deps
