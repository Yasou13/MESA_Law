from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy
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
    db: AsyncSession = Depends(get_db),
):
    if not settings.external_research_enabled:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=501, detail="External legal research is disabled in the MVP"
        )
    await MatterAccessPolicy.can_write(context, db, payload.matter_id)
    from apps.api.models.queue import Job

    job = Job(
        type="PERFORM_LEGAL_RESEARCH",
        tenant_id=context.tenant_id,
        payload={
            "matter_id": payload.matter_id,
            "query": payload.query,
            "tenant_id": context.tenant_id,
        },
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


@router.get(
    "/search",
    response_model=list[LegalSourceResponse],
    operation_id="searchLegalResearch",
)
@limiter.limit("60/minute")
async def search_legal_research(
    request: Request,
    q: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if not settings.external_research_enabled:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=501, detail="External legal research is disabled in the MVP"
        )
    from apps.api.models.document import Document
    from apps.api.models.domain import MatterMember

    # 1. Search external sources
    stmt_external = (
        select(LegalSource)
        .where(
            or_(
                LegalSource.title.ilike(f"%{q}%"),
                LegalSource.content.ilike(f"%{q}%"),
                LegalSource.citation.ilike(f"%{q}%"),
            )
        )
        .limit(10)
    )

    result_ext = await db.execute(stmt_external)
    sources = result_ext.scalars().all()

    # 2. Search internal firm documents (as precedent)
    stmt_internal = (
        select(Document)
        .join(
            MatterMember,
            (MatterMember.matter_id == Document.matter_id)
            & (MatterMember.user_id == context.principal_id),
        )
        .where(
            Document.tenant_id == context.tenant_id,
            MatterMember.tenant_id == context.tenant_id,
            Document.title.ilike(f"%{q}%"),
        )
        .limit(10)
    )

    result_int = await db.execute(stmt_internal)
    internal_docs = result_int.scalars().all()

    responses = [
        {
            "id": s.id,
            "title": s.title,
            "citation": s.citation,
            "source_type": s.source_type,
            "content": s.content[:500] + "..." if len(s.content) > 500 else s.content,
        }
        for s in sources
    ]

    for d in internal_docs:
        responses.append(
            {
                "id": d.id,
                "title": d.title,
                "citation": f"Internal Doc: {d.id[:8]}",
                "source_type": "internal_precedent",
                "content": f"Internal document uploaded to matter {d.matter_id}. Title: {d.title}",
            }
        )

    return responses
