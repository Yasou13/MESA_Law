
from apps.api.core.database import get_db
from apps.api.core.factory import get_intelligence_adapter
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import Matter
from apps.api.schemas.api import MatterCreate, MatterResponse
from apps.api.services.mesa_sync import MesaSyncService
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.ratelimit import limiter

router = APIRouter()

@router.get("", response_model=list[MatterResponse], operation_id="listMatters")
@limiter.limit("100/minute")
async def list_matters(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Matter).where(Matter.tenant_id == context.tenant_id).order_by(Matter.created_at.desc()))
    matters = result.scalars().all()
    return [{"id": m.id, "title": m.title, "status": m.status} for m in matters]

@router.post("", response_model=MatterResponse, operation_id="createMatter")
@limiter.limit("30/minute")
async def create_matter(
    request: Request,
    matter_data: MatterCreate,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    matter = Matter(title=matter_data.title, tenant_id=context.tenant_id)
    db.add(matter)
    await db.commit()
    await db.refresh(matter)
    return {"id": matter.id, "title": matter.title, "status": matter.status}

@router.post("/{matter_id}/rebuild-mesa", operation_id="rebuildMatterMesa")
@limiter.limit("5/minute")
async def rebuild_matter_mesa(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    adapter = get_intelligence_adapter()
    service = MesaSyncService(adapter)
    try:
        synced = await service.sync_matter(db, context.tenant_id, matter_id)
        return {"status": "success", "synced_pages": synced}
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()
