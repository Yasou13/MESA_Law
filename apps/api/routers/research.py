from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.core.ratelimit import limiter
from apps.api.models.research import LegalSource

router = APIRouter(tags=["research"])

from pydantic import BaseModel

class ResearchRequest(BaseModel):
    matter_id: str
    query: str

@router.post("/start", operation_id="startLegalResearch")
@limiter.limit("20/minute")
async def start_legal_research(
    request: Request,
    payload: ResearchRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    from apps.api.models.queue import Job
    job = Job(
        type="PERFORM_LEGAL_RESEARCH",
        payload={
            "matter_id": payload.matter_id,
            "query": payload.query,
            "tenant_id": context.tenant_id
        }
    )
    db.add(job)
    await db.commit()
    return {"status": "accepted", "job_id": job.id}

