from datetime import UTC, datetime

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import MatterMember
from apps.api.models.mesa import MesaSyncRecord
from apps.api.models.queue import Job, JobStatus
from apps.api.models.review import ReviewItem, ReviewState
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, exists, func, select
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


class OperationalMetricsResponse(BaseModel):
    job_queue_depth: int
    stale_job_leases: int
    document_pipeline_failures: int
    review_backlog: int
    mesa_mutation_terminal_statuses: dict[str, int]


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


@router.get(
    "/metrics",
    response_model=OperationalMetricsResponse,
    operation_id="getOperationalMetrics",
)
async def get_operational_metrics(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(setup_tenant_context),
) -> OperationalMetricsResponse:
    """Return bounded, tenant- and matter-scoped operational snapshots."""

    def member_can_access(model):
        return exists(
            select(MatterMember.id).where(
                MatterMember.matter_id == model.matter_id,
                MatterMember.tenant_id == context.tenant_id,
                MatterMember.user_id == context.principal_id,
            )
        )

    job_scope = (
        Job.tenant_id == context.tenant_id,
        Job.matter_id.is_not(None),
        member_can_access(Job),
    )
    queue_depth = await db.scalar(
        select(func.count(Job.id)).where(
            *job_scope,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
    )
    stale_leases = await db.scalar(
        select(func.count(Job.id)).where(
            *job_scope,
            Job.status == JobStatus.RUNNING,
            Job.locked_until < datetime.now(UTC),
        )
    )
    pipeline_failures = await db.scalar(
        select(func.count(Job.id)).where(
            *job_scope,
            Job.type.in_(
                [
                    "SCAN_DOCUMENT",
                    "PARSE_DOCUMENT",
                    "OCR_DOCUMENT",
                    "EXTRACT_LEGAL_DATA",
                    "EXTRACT_LEGAL_FACTS",
                ]
            ),
            Job.status.in_([JobStatus.FAILED, JobStatus.DEAD]),
        )
    )
    review_backlog = await db.scalar(
        select(func.count(ReviewItem.id)).where(
            ReviewItem.tenant_id == context.tenant_id,
            ReviewItem.status == ReviewState.PROPOSED,
            member_can_access(ReviewItem),
        )
    )
    mutation_rows = (
        await db.execute(
            select(MesaSyncRecord.status, func.count(MesaSyncRecord.id))
            .where(
                MesaSyncRecord.tenant_id == context.tenant_id,
                MesaSyncRecord.is_terminal.is_(True),
                member_can_access(MesaSyncRecord),
            )
            .group_by(MesaSyncRecord.status)
        )
    ).all()

    return OperationalMetricsResponse(
        job_queue_depth=queue_depth or 0,
        stale_job_leases=stale_leases or 0,
        document_pipeline_failures=pipeline_failures or 0,
        review_backlog=review_backlog or 0,
        mesa_mutation_terminal_statuses={
            str(status): count for status, count in mutation_rows
        },
    )
