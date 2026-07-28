from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select

from apps.api.dependencies.auth import setup_tenant_context
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.models.queue import Job
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter(prefix="/operations", tags=["Operations"])

class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    tenant_id: str
    matter_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    retries: int
    max_retries: int
    payload: dict

    model_config = ConfigDict(from_attributes=True)

@router.get("/jobs", response_model=List[JobResponse], operation_id="listJobs")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(setup_tenant_context),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List background worker jobs.
    """
    query = select(Job)
    
    if getattr(context, "role", "") != "SYS_ADMIN":
        query = query.where(Job.tenant_id == context.tenant_id)
        
    query = query.order_by(desc(Job.created_at)).limit(limit)
    res = await db.execute(query)
    jobs = res.scalars().all()
    return jobs
