from apps.api.core.database import get_db
from apps.api.core.factory import get_intelligence_adapter
from apps.api.core.models import RequestContext
from apps.api.core.policies import AdminAccessPolicy, MatterAccessPolicy
from apps.api.core.ratelimit import limiter
from apps.api.dependencies.auth import require_recent_auth, setup_tenant_context
from apps.api.models.domain import Matter
from apps.api.schemas.api import MatterCreate, MatterResponse
from apps.api.services.mesa_sync import MesaSyncService
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("", response_model=list[MatterResponse], operation_id="listMatters")
@limiter.limit("100/minute")
async def list_matters(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    await MatterAccessPolicy.can_read(context, db)
    from apps.api.models.domain import MatterMember, Role
    
    # Firm admins have 'admin' scope on all matters implicitly
    user_roles = {r.value if hasattr(r, 'value') else r for r in context.roles}
    is_admin = Role.FIRM_ADMIN.value in user_roles
    
    if is_admin:
        stmt = select(Matter, MatterMember.access_scope).outerjoin(
            MatterMember, 
            (Matter.id == MatterMember.matter_id) & (MatterMember.user_id == context.principal_id)
        ).where(Matter.tenant_id == context.tenant_id).order_by(Matter.created_at.desc())
    else:
        stmt = select(Matter, MatterMember.access_scope).join(
            MatterMember, 
            (Matter.id == MatterMember.matter_id) & (MatterMember.user_id == context.principal_id)
        ).where(Matter.tenant_id == context.tenant_id).order_by(Matter.created_at.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        {
            "id": m.id, 
            "title": m.title, 
            "internal_reference": m.internal_reference,
            "status": m.status, 
            "client_name": m.client_name,
            "jurisdiction": m.jurisdiction,
            "case_type": m.case_type,
            "confidentiality_level": m.confidentiality_level,
            "ai_processing_policy": m.ai_processing_policy,
            "opened_at": m.opened_at.isoformat() if m.opened_at else None,
            "closed_at": m.closed_at.isoformat() if m.closed_at else None,
            "access_scope": "admin" if is_admin else (scope or "read")
        } for m, scope in rows
    ]

from apps.api.core.idempotency import check_idempotency, complete_idempotency
from fastapi import Header


@router.get("/{matter_id}", response_model=MatterResponse, operation_id="getMatter")
@limiter.limit("100/minute")
async def get_matter(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    
    matter = await db.get(Matter, matter_id)
    if not matter or matter.tenant_id != context.tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Matter not found")
        
    # Get user's scope
    from apps.api.models.domain import MatterMember, Role
    user_roles = {r.value if hasattr(r, 'value') else r for r in context.roles}
    is_admin = Role.FIRM_ADMIN.value in user_roles
    
    scope = "admin"
    if not is_admin:
        stmt = select(MatterMember.access_scope).where(
            MatterMember.matter_id == matter_id,
            MatterMember.user_id == context.principal_id,
            MatterMember.tenant_id == context.tenant_id
        )
        res = await db.execute(stmt)
        scope = res.scalar() or "read"
        
    return {
        "id": matter.id, 
        "title": matter.title, 
        "internal_reference": matter.internal_reference,
        "status": matter.status, 
        "client_name": matter.client_name,
        "jurisdiction": matter.jurisdiction,
        "case_type": matter.case_type,
        "confidentiality_level": matter.confidentiality_level,
        "ai_processing_policy": matter.ai_processing_policy,
        "opened_at": matter.opened_at.isoformat() if matter.opened_at else None,
        "closed_at": matter.closed_at.isoformat() if matter.closed_at else None,
        "access_scope": scope
    }

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
            
    await MatterAccessPolicy.can_create(context)
    matter = Matter(
        title=matter_data.title, 
        internal_reference=matter_data.internal_reference,
        client_name=matter_data.client_name,
        tenant_id=context.tenant_id,
        jurisdiction=matter_data.jurisdiction,
        case_type=matter_data.case_type,
        confidentiality_level=matter_data.confidentiality_level,
        ai_processing_policy=matter_data.ai_processing_policy,
        responsible_attorney_id=context.principal_id,
        opened_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
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
    
    resp = {
        "id": matter.id, 
        "title": matter.title, 
        "internal_reference": matter.internal_reference,
        "status": matter.status,
        "client_name": matter.client_name,
        "jurisdiction": matter.jurisdiction,
        "case_type": matter.case_type,
        "confidentiality_level": matter.confidentiality_level,
        "ai_processing_policy": matter.ai_processing_policy,
        "opened_at": matter.opened_at.isoformat() if matter.opened_at else None,
        "closed_at": matter.closed_at.isoformat() if matter.closed_at else None,
        "access_scope": "admin"
    }
    
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
    await MatterAccessPolicy.can_read(context, db, matter_id)
    question = query.get("question")
    if not question:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing question in body")
        
    return await ask_matter_question(db, context.tenant_id, matter_id, None, question)

class MatterPartyResponse(BaseModel):
    id: str
    name: str
    role: str
    type: str

@router.get("/{matter_id}/parties", response_model=list[MatterPartyResponse], operation_id="listMatterParties")
async def list_matter_parties(
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    from apps.api.models.domain import MatterParty
    result = await db.execute(select(MatterParty).where(MatterParty.matter_id == matter_id))
    return result.scalars().all()

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
    id: str
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
    await MatterAccessPolicy.can_read(context, db)
    
    from apps.api.models.domain import Matter, MatterParty
    from sqlalchemy import select
    
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
            
    from apps.api.models.domain import ConflictCheckResult
    
    check_record = ConflictCheckResult(
        tenant_id=context.tenant_id,
        requested_by=context.principal_id,
        party_names=payload.party_names,
        has_conflicts=len(results) > 0,
        results=[r.model_dump() for r in results]
    )
    db.add(check_record)
    await db.commit()
    await db.refresh(check_record)
            
    return ConflictCheckResponse(id=check_record.id, conflicts=results, has_conflicts=len(results) > 0)

class OverrideConflictRequest(BaseModel):
    reason: str

@router.post("/{matter_id}/override-conflict", operation_id="overrideConflict")
@limiter.limit("5/minute")
async def override_conflict(
    request: Request,
    matter_id: str,
    payload: OverrideConflictRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_recent_auth)
):
    await MatterAccessPolicy.can_create(context)
    
    # Normally we'd log the reason to the matter metadata or an audit trail.
    matter = await db.get(Matter, matter_id)
    if not matter or matter.tenant_id != context.tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Matter not found")
        
    # Mark as overridden in metadata
    if not matter.metadata_info:
        matter.metadata_info = {}
    matter.metadata_info["conflict_overridden"] = True
    matter.metadata_info["conflict_override_reason"] = payload.reason
    matter.metadata_info["conflict_override_by"] = context.principal_id
    
    await db.commit()
    return {"status": "success", "message": "Conflict check overridden"}
