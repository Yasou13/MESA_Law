from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from pydantic import BaseModel

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.deadline import ApprovedDeadline

router = APIRouter(tags=["Deadlines"])

class DeadlineResponse(BaseModel):
    id: str
    matter_id: str
    due_date: date
    description: str
    is_completed: bool

@router.get("", response_model=list[DeadlineResponse], operation_id="listDeadlines")
async def list_deadlines(
    matter_id: str | None = None,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    query = select(ApprovedDeadline).where(
        ApprovedDeadline.tenant_id == context.tenant_id,
        ApprovedDeadline.is_completed == False
    ).order_by(ApprovedDeadline.due_date.asc())
    
    if matter_id:
        query = query.where(ApprovedDeadline.matter_id == matter_id)
        
    result = await db.execute(query)
    deadlines = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "matter_id": d.matter_id,
            "due_date": d.due_date,
            "description": d.description,
            "is_completed": d.is_completed
        } for d in deadlines
    ]

@router.post("/{deadline_id}/complete", operation_id="completeDeadline")
async def complete_deadline(
    deadline_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    deadline = await db.get(ApprovedDeadline, deadline_id)
    if not deadline or deadline.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Deadline not found")
        
    deadline.is_completed = True
    await db.commit()
    
    return {"status": "success"}
