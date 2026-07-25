from fastapi import APIRouter, Depends
from pydantic import BaseModel
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.draft import Draft
from apps.api.models.queue import Job
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

router = APIRouter(prefix="/draft-studio", tags=["draft-studio"])

class SaveDraftRequest(BaseModel):
    matter_id: str
    title: str
    content: str

class ExportDraftRequest(BaseModel):
    format: str # 'pdf' or 'docx'

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
        content=payload.content
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return {"id": draft.id, "version": draft.version}

@router.post("/drafts/{draft_id}/export")
async def export_draft(
    request: Request,
    draft_id: str,
    payload: ExportDraftRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Queue worker job for exporting
    job = Job(
        type="EXPORT_DRAFT",
        payload={
            "draft_id": draft_id,
            "format": payload.format
        }
    )
    db.add(job)
    await db.commit()
    return {"message": "Export job queued", "job_id": job.id}
