from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.draft import Draft
from apps.api.models.queue import Job

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
    return {"id": draft.id, "version": draft.version, "title": draft.title, "content": draft.content}

@router.get("/drafts/matter/{matter_id}")
async def list_matter_drafts(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Draft).where(Draft.matter_id == matter_id, Draft.tenant_id == context.tenant_id).order_by(Draft.updated_at.desc())
    result = await db.execute(stmt)
    drafts = result.scalars().all()
    return [
        {
            "id": d.id,
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
    return {
        "id": draft.id,
        "matter_id": draft.matter_id,
        "title": draft.title,
        "content": draft.content,
        "version": draft.version,
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
    draft = await db.get(Draft, draft_id)
    if not draft or draft.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    if payload.expected_version is not None and draft.version != payload.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict: draft has been modified by another process")
        
    if payload.title is not None:
        draft.title = payload.title
    if payload.content is not None:
        draft.content = payload.content
        
    draft.version += 1
    await db.commit()
    await db.refresh(draft)
    return {"id": draft.id, "version": draft.version, "title": draft.title, "content": draft.content}

@router.post("/drafts/{draft_id}/export")
async def export_draft(
    request: Request,
    draft_id: str,
    payload: ExportDraftRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    draft = await db.get(Draft, draft_id)
    if not draft or draft.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    job = Job(
        type="EXPORT_DRAFT",
        payload={
            "draft_id": draft_id,
            "format": payload.format
        }
    )
    db.add(job)
    await db.commit()
    return {"message": "Export job queued", "job_id": job.id, "format": payload.format, "version": draft.version}
