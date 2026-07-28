from datetime import UTC, datetime

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.audit import Notification
from apps.api.models.deadline import ApprovedDeadline
from apps.api.models.domain import Matter
from apps.api.models.queue import Job
from apps.api.models.review import ReviewItem
from apps.api.routers.system import get_dependencies
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Dashboard"])

@router.get("/api/v1/dashboard/metrics")
async def get_dashboard_metrics(
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = context.tenant_id

    # Active Matters
    matters_count = await db.scalar(
        select(func.count(Matter.id)).where(Matter.tenant_id == tenant_id, Matter.status == "open")
    )

    # Pending Reviews
    reviews_count = await db.scalar(
        select(func.count(ReviewItem.id)).where(ReviewItem.status == "pending")
    )

    # Upcoming Deadlines
    now = datetime.now(UTC)
    deadlines_count = await db.scalar(
        select(func.count(ApprovedDeadline.id)).where(
            ApprovedDeadline.tenant_id == tenant_id,
            ApprovedDeadline.due_date >= now
        )
    )

    # Unread Notifications
    notifs_count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.tenant_id == tenant_id,
            Notification.status == "CREATED"
        )
    )
    
    # Failed Operations
    failed_ops = await db.scalar(
        select(func.count(Job.id)).where(
            Job.tenant_id == tenant_id,
            Job.status == "failed"
        )
    )
    
    # Degraded Capabilities
    deps = await get_dependencies(db)
    degraded = [k for k, v in deps.items() if v not in ("ok", "down")]

    return {
        "active_matters": matters_count or 0,
        "pending_reviews": reviews_count or 0,
        "upcoming_deadlines": deadlines_count or 0,
        "unread_notifications": notifs_count or 0,
        "failed_operations": failed_ops or 0,
        "degraded_capabilities": degraded,
        "system_status": "ok" if not degraded else "degraded"
    }
