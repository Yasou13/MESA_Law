from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select

from apps.api.dependencies.auth import setup_tenant_context
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.models.audit import AuditEvent
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter(prefix="/audit", tags=["Audit"])

class AuditEventResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    changes: Optional[dict] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/events", response_model=List[AuditEventResponse], operation_id="listAuditEvents")
async def list_audit_events(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(setup_tenant_context),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List audit events.
    """
    query = select(AuditEvent).where(AuditEvent.tenant_id == context.tenant_id)
    query = query.order_by(desc(AuditEvent.timestamp)).limit(limit)
    res = await db.execute(query)
    events = res.scalars().all()
    return events
