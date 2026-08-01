import asyncio
import json
from datetime import datetime

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import get_current_user, setup_tenant_context
from apps.api.models.audit import Notification
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    category: str
    title: str
    message: str
    status: str
    timestamp: datetime


@router.get("/sse")
async def sse_endpoint(
    request: Request,
    user: dict = Depends(get_current_user),
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Server-Sent Events endpoint for real-time notifications.
    """

    async def event_generator():
        last_notif_id = None

        while True:
            # If client disconnects, stop
            if await request.is_disconnected():
                break

            # Query for new notifications (simplified polling)
            stmt = select(Notification).where(
                Notification.tenant_id == context.tenant_id,
                Notification.user_id == context.principal_id,
                Notification.status == "CREATED",
            )
            result = await db.execute(stmt)
            new_notifs = result.scalars().all()

            for notif in new_notifs:
                if notif.id != last_notif_id:
                    yield {
                        "event": "notification",
                        "id": notif.id,
                        "retry": 15000,
                        "data": json.dumps(
                            {
                                "id": notif.id,
                                "category": notif.category,
                                "title": notif.title,
                                "message": notif.message,
                                "timestamp": notif.timestamp.isoformat(),
                            }
                        ),
                    }
                    last_notif_id = notif.id

                    # Mark as DELIVERED
                    notif.status = "DELIVERED"

            if new_notifs:
                await db.commit()

            await asyncio.sleep(5)  # Poll every 5 seconds

    return EventSourceResponse(event_generator())


@router.get(
    "", response_model=list[NotificationResponse], operation_id="listNotifications"
)
async def get_notifications(
    request: Request,
    user: dict = Depends(get_current_user),
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all notifications for the current tenant and user.
    """
    stmt = (
        select(Notification)
        .where(
            Notification.tenant_id == context.tenant_id,
            Notification.user_id == context.principal_id,
        )
        .order_by(Notification.timestamp.desc())
    )

    result = await db.execute(stmt)
    notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "category": n.category,
            "title": n.title,
            "message": n.message,
            "status": n.status,
            "timestamp": n.timestamp.isoformat(),
        }
        for n in notifications
    ]
