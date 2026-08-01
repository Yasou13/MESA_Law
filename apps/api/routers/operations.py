from datetime import datetime

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import MatterMember
from apps.api.models.queue import Job
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/operations", tags=["Operations"])


class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    tenant_id: str
    matter_id: str | None = None
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
    retries: int
    max_retries: int
    payload: dict

    model_config = ConfigDict(from_attributes=True)


@router.get("/jobs", response_model=list[JobResponse], operation_id="listJobs")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(setup_tenant_context),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List background worker jobs.
    """
    query = (
        select(Job)
        .join(
            MatterMember,
            (MatterMember.matter_id == Job.matter_id)
            & (MatterMember.user_id == context.principal_id),
        )
        .where(
            Job.tenant_id == context.tenant_id,
            MatterMember.tenant_id == context.tenant_id,
        )
    )

    query = query.order_by(desc(Job.created_at)).limit(limit)
    res = await db.execute(query)
    jobs = res.scalars().all()
    return jobs
