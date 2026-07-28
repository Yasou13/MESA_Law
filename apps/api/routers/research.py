from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.ratelimit import limiter
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.research import LegalSource
from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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

class LegalSourceResponse(BaseModel):
    id: str
    title: str
    citation: str
    source_type: str
    content: str
    
@router.get("/search", response_model=list[LegalSourceResponse], operation_id="searchLegalResearch")
@limiter.limit("60/minute")
async def search_legal_research(
    request: Request,
    q: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LegalSource).where(
        or_(
            LegalSource.title.ilike(f"%{q}%"),
            LegalSource.content.ilike(f"%{q}%"),
            LegalSource.citation.ilike(f"%{q}%")
        )
    ).limit(20)
    
    result = await db.execute(stmt)
    sources = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "title": s.title,
            "citation": s.citation,
            "source_type": s.source_type,
            "content": s.content[:500] + "..." if len(s.content) > 500 else s.content
        } for s in sources
    ]

