import asyncio
import json
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.audit import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

# In a real distributed app, we would use Redis PubSub.
# For single-worker / MVP setup, we can poll DB or use a local asyncio.Event trigger.
# To satisfy the audit phase without overengineering, we'll do DB polling for new notifications.

@router.get("/sse")
async def sse_endpoint(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
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
                Notification.status == "CREATED"
            )
            
            # Note: in real app, filter by user_id too if context has user_id
            
            result = await db.execute(stmt)
            new_notifs = result.scalars().all()
            
            for notif in new_notifs:
                if notif.id != last_notif_id:
                    yield {
                        "event": "notification",
                        "id": notif.id,
                        "retry": 15000,
                        "data": json.dumps({
                            "id": notif.id,
                            "category": notif.category,
                            "title": notif.title,
                            "message": notif.message,
                            "timestamp": notif.timestamp.isoformat()
                        })
                    }
                    last_notif_id = notif.id
                    
                    # Mark as DELIVERED
                    notif.status = "DELIVERED"
            
            if new_notifs:
                await db.commit()
                
            await asyncio.sleep(5)  # Poll every 5 seconds
            
    return EventSourceResponse(event_generator())

@router.get("")
async def get_notifications(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all notifications for the current tenant.
    """
    stmt = select(Notification).where(
        Notification.tenant_id == context.tenant_id
    ).order_by(Notification.timestamp.desc())
    
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    
    return [
        {
            "id": n.id,
            "category": n.category,
            "title": n.title,
            "message": n.message,
            "status": n.status,
            "timestamp": n.timestamp.isoformat()
        } for n in notifications
    ]
