from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import (
    DraftAccessPolicy,
    ExportAccessPolicy,
    MatterAccessPolicy,
)
from apps.api.dependencies.auth import setup_tenant_context, require_recent_auth
from apps.api.models.draft import Draft
from apps.api.models.queue import Job
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/draft-studio", tags=["draft-studio"])

class SaveDraftRequest(BaseModel):
    matter_id: str
    title: str
    content: str

class UpdateDraftRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    expected_version: int | None = None

class ExportDraftRequest(BaseModel):
    format: str  # 'pdf' or 'docx'

@router.post("/drafts")
async def save_draft(
    request: Request,
    payload: SaveDraftRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    DraftAccessPolicy.can_manage(context)
    draft = Draft(
        tenant_id=context.tenant_id,
        matter_id=payload.matter_id,
        title=payload.title,
        content=payload.content,
        version=1
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return {"id": draft.id, "version": draft.version, "title": draft.title, "content": draft.content, "status": draft.status}

@router.get("/drafts/matter/{matter_id}")
async def list_matter_drafts(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    MatterAccessPolicy.can_read(context, matter_id)
    stmt = select(Draft).where(Draft.matter_id == matter_id, Draft.tenant_id == context.tenant_id).order_by(Draft.updated_at.desc())
    result = await db.execute(stmt)
    drafts = result.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "version": d.version,
            "status": d.status,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None
        }
        for d in drafts
    ]

@router.get("/drafts")
async def list_all_drafts(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    MatterAccessPolicy.can_read(context)
    stmt = select(Draft).where(Draft.tenant_id == context.tenant_id).order_by(Draft.updated_at.desc())
    result = await db.execute(stmt)
    drafts = result.scalars().all()
    return [
        {
            "id": d.id,
            "matter_id": d.matter_id,
            "title": d.title,
            "version": d.version,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None
        }
        for d in drafts
    ]

@router.get("/drafts/{draft_id}")
async def get_draft(
    request: Request,
    draft_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    draft = await db.get(Draft, draft_id)
    if not draft or draft.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    MatterAccessPolicy.can_read(context, draft.matter_id)
        
    return {
        "id": draft.id,
        "matter_id": draft.matter_id,
        "title": draft.title,
        "content": draft.content,
        "version": draft.version,
        "status": draft.status,
        "updated_at": draft.updated_at.isoformat() if draft.updated_at else None
    }

@router.put("/drafts/{draft_id}")
async def update_draft(
    request: Request,
    draft_id: str,
    payload: UpdateDraftRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    from apps.api.models.draft import DraftRevision
    
    draft = await db.get(Draft, draft_id)
    if not draft or draft.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    DraftAccessPolicy.can_manage(context)
        
    # Phase 11: If-Match ETag checking
    if_match = request.headers.get("if-match")
    if if_match and if_match.strip('"') != draft.etag:
        raise HTTPException(status_code=412, detail="VERSION_CONFLICT: ETag mismatch")
        
    # Also support body expected_version
    if payload.expected_version is not None and draft.version != payload.expected_version:
        raise HTTPException(status_code=409, detail="VERSION_CONFLICT: Draft has been modified by another process")
        
    # 1. Save old content as a DraftRevision
    old_revision = DraftRevision(
        tenant_id=context.tenant_id,
        draft_id=draft.id,
        version=draft.version,
        content=draft.content,
        change_summary="Auto-saved revision prior to update"
    )
    db.add(old_revision)
        
    # 2. Update Draft
    if payload.title is not None:
        draft.title = payload.title
    if payload.content is not None:
        draft.content = payload.content
        
    if draft.status == "APPROVED_FOR_EXTERNAL_USE":
        draft.status = "DRAFT"
        
    draft.version += 1
    draft.etag = f"v{draft.version}"
    
    await db.commit()
    await db.refresh(draft)
    
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"id": draft.id, "version": draft.version, "title": draft.title, "content": draft.content, "status": draft.status, "etag": draft.etag})
    response.headers["ETag"] = f'"{draft.etag}"'
    return response

@router.post("/drafts/{draft_id}/approve", operation_id="approveDraft")
async def approve_draft(
    request: Request,
    draft_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_recent_auth)
):
    draft = await db.get(Draft, draft_id)
    if not draft or draft.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    DraftAccessPolicy.can_approve_external(context)
        
    from apps.api.models.draft import DraftCitation
    from sqlalchemy import select
    stmt = select(DraftCitation).where(DraftCitation.draft_id == draft_id)
    citations = await db.execute(stmt)
    for citation in citations.scalars():
        if citation.verification_state in ["unverified", "STALE_REVISION"]:
            raise HTTPException(status_code=403, detail=f"Cannot approve draft. Contains {citation.verification_state} citations.")
            
    draft.status = "APPROVED_FOR_EXTERNAL_USE"
    await db.commit()
    return {"status": draft.status}

@router.post("/drafts/{draft_id}/export")
async def export_draft(
    request: Request,
    draft_id: str,
    payload: ExportDraftRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        from apps.api.core.idempotency import check_idempotency, complete_idempotency
        cached = await check_idempotency(db, idem_key)
        if cached:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=cached.status_code or 200, content=cached.response_body)
            
    draft = await db.get(Draft, draft_id)
    if not draft or draft.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    ExportAccessPolicy.can_export(context)
        
    if payload.format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="MIME Error: Only 'pdf' and 'docx' formats are supported")
        
    if draft.status != "APPROVED_FOR_EXTERNAL_USE":
        raise HTTPException(status_code=403, detail="Draft must be APPROVED_FOR_EXTERNAL_USE to be exported")
        
    from apps.api.models.draft import DraftCitation
    stmt = select(DraftCitation).where(DraftCitation.draft_id == draft_id, DraftCitation.verification_state == "unverified")
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=403, detail="Draft cannot be exported while containing UNVERIFIED citations")
        
    job = Job(
        type="EXPORT_DRAFT",
        payload={
            "draft_id": draft_id,
            "format": payload.format
        }
    )
    db.add(job)
    await db.commit()
    
    resp_body = {"message": "Export job queued", "job_id": job.id, "format": payload.format, "version": draft.version}
    if idem_key:
        await complete_idempotency(db, idem_key, 200, resp_body)
        
    return resp_body

class GenerateDraftRequest(BaseModel):
    matter_id: str
    template_name: str | None = None

@router.post("/drafts/generate")
async def generate_draft(
    request: Request,
    payload: GenerateDraftRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    DraftAccessPolicy.can_manage(context)
    job = Job(
        type="GENERATE_DRAFT",
        payload={
            "tenant_id": context.tenant_id,
            "matter_id": payload.matter_id,
            "template_name": payload.template_name or "default"
        }
    )
    db.add(job)
    await db.commit()
    return {"message": "Draft generation job queued", "job_id": job.id}
