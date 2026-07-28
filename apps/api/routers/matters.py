from pydantic import BaseModel
from apps.api.core.database import get_db
from apps.api.core.factory import get_intelligence_adapter
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import Matter
from apps.api.schemas.api import MatterCreate, MatterResponse
from apps.api.core.policies import MatterAccessPolicy, AdminAccessPolicy
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
    MatterAccessPolicy.can_read(context)
    result = await db.execute(select(Matter).where(Matter.tenant_id == context.tenant_id).order_by(Matter.created_at.desc()))
    matters = result.scalars().all()
    return [{"id": m.id, "title": m.title, "status": m.status} for m in matters]

from fastapi import Header
from apps.api.core.idempotency import check_idempotency, complete_idempotency

@router.post("", response_model=MatterResponse, operation_id="createMatter", status_code=201)
@limiter.limit("30/minute")
async def create_matter(
    request: Request,
    matter_data: MatterCreate,
    idem_key: str | None = Header(None, alias="Idempotency-Key"),
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    if idem_key:
        cached = await check_idempotency(db, idem_key)
        if cached and cached.response_body:
            return cached.response_body
            
    MatterAccessPolicy.can_create(context)
    matter = Matter(
        title=matter_data.title, 
        tenant_id=context.tenant_id,
        jurisdiction=matter_data.jurisdiction,
        confidentiality_level=matter_data.confidentiality_level,
        lead_attorney_id=context.principal_id
    )
    db.add(matter)
    await db.flush()
    
    from apps.api.models.domain import MatterMember
    member = MatterMember(
        matter_id=matter.id,
        user_id=context.principal_id,
        access_scope="admin",
        tenant_id=context.tenant_id
    )
    db.add(member)
    
    await db.commit()
    await db.refresh(matter)
    
    resp = {"id": matter.id, "title": matter.title, "status": matter.status}
    
    if idem_key:
        await complete_idempotency(db, idem_key, 201, resp)
        
    return resp

@router.post("/{matter_id}/rebuild-mesa", operation_id="rebuildMatterMesa")
@limiter.limit("5/minute")
async def rebuild_matter_mesa(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    adapter = get_intelligence_adapter()
    AdminAccessPolicy.can_rebuild_mesa(context)
    service = MesaSyncService(adapter)
    try:
        synced = await service.sync_matter(db, context.tenant_id, matter_id)
        return {"status": "success", "synced_pages": synced}
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()

from apps.api.core.qa import ask_matter_question

@router.post("/{matter_id}/qa", operation_id="matterQA")
@limiter.limit("20/minute")
async def matter_qa_endpoint(
    request: Request,
    matter_id: str,
    query: dict,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    MatterAccessPolicy.can_read(context, matter_id)
    question = query.get("question")
    if not question:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing question in body")
        
    return await ask_matter_question(db, matter_id, question)

class ConflictCheckRequest(BaseModel):
    party_names: list[str]

class ConflictResult(BaseModel):
    searched_name: str
    matched_name: str
    role: str
    matter_id: str
    matter_title: str
    status: str

class ConflictCheckResponse(BaseModel):
    has_conflicts: bool
    conflicts: list[ConflictResult]

@router.post("/conflict-check", response_model=ConflictCheckResponse, operation_id="conflictCheck")
@limiter.limit("20/minute")
async def check_conflicts(
    request: Request,
    payload: ConflictCheckRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    MatterAccessPolicy.can_read(context)
    
    from sqlalchemy import select, or_, and_
    from apps.api.models.domain import MatterParty, Matter
    
    results = []
    for party_name in payload.party_names:
        stmt = select(MatterParty, Matter).join(Matter, MatterParty.matter_id == Matter.id).where(
            MatterParty.tenant_id == context.tenant_id,
            MatterParty.name.ilike(f"%{party_name}%")
        )
        res = await db.execute(stmt)
        matches = res.all()
        for mp, m in matches:
            results.append(ConflictResult(
                searched_name=party_name,
                matched_name=mp.name,
                role=mp.role,
                matter_id=m.id,
                matter_title=m.title,
                status=m.status
            ))
            
    return ConflictCheckResponse(conflicts=results, has_conflicts=len(results) > 0)
