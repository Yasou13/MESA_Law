import os
import socket
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.api.core.database import get_db

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
async def system_dependencies(db: AsyncSession = Depends(get_db)):
    return await get_dependencies(db)

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
        deps["intelligence_adapter"] = "ok"
    else:
        deps["intelligence_adapter"] = "degraded"

    return deps
