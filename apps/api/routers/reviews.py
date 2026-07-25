from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import timedelta
from pydantic import BaseModel

from apps.api.core.database import get_db
from apps.api.core.storage import storage_service
from apps.api.main import setup_tenant_context
from apps.api.models.review import ReviewQueue, AuditLog
from apps.api.core.utils import utc_now

router = APIRouter(prefix="/reviews", tags=["reviews"])

class ReviewItemResponse(BaseModel):
    id: str
    matter_id: str
    entity_type: str
    entity_id: str
    proposed_content: dict
    status: str

class CorrectReviewRequest(BaseModel):
    corrected_content: dict

@router.get("", response_model=List[ReviewItemResponse])
async def list_pending_reviews(
    matter_id: Optional[str] = None,
    context: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    query = select(ReviewQueue).where(
        ReviewQueue.tenant_id == context,
        ReviewQueue.status == "pending"
    )
    if matter_id:
        query = query.where(ReviewQueue.matter_id == matter_id)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{review_id}/approve")
async def approve_review(
    review_id: str,
    context: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReviewQueue).where(ReviewQueue.id == review_id, ReviewQueue.tenant_id == context))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    if review.status != "pending":
        raise HTTPException(status_code=400, detail="Item is not pending review")
        
    review.status = "approved"
    review.reviewed_by = context.user_id
    review.reviewed_at = utc_now()
    
    # Solo mode policy: cooling-off period of 2 hours for external use
    review.external_use_ready_at = utc_now() + timedelta(hours=2)
    
    # Create immutable audit log
    audit = AuditLog(
        tenant_id=context,
        matter_id=review.matter_id,
        user_id=context.user_id,
        action="APPROVE_REVIEW",
        entity_type=review.entity_type,
        entity_id=review.entity_id,
        details={"original_content": review.proposed_content}
    )
    db.add(audit)
    
    await db.commit()
    return {"status": "success", "message": "Review approved with 2-hour cooling-off period for external use"}

@router.post("/{review_id}/reject")
async def reject_review(
    review_id: str,
    context: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReviewQueue).where(ReviewQueue.id == review_id, ReviewQueue.tenant_id == context))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
        
    review.status = "rejected"
    review.reviewed_by = context.user_id
    review.reviewed_at = utc_now()
    
    audit = AuditLog(
        tenant_id=context,
        matter_id=review.matter_id,
        user_id=context.user_id,
        action="REJECT_REVIEW",
        entity_type=review.entity_type,
        entity_id=review.entity_id,
        details={"original_content": review.proposed_content}
    )
    db.add(audit)
    
    await db.commit()
    return {"status": "success", "message": "Review rejected"}

@router.post("/{review_id}/correct")
async def correct_review(
    review_id: str,
    request: CorrectReviewRequest,
    context: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReviewQueue).where(ReviewQueue.id == review_id, ReviewQueue.tenant_id == context))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
        
    review.status = "corrected"
    review.corrected_content = request.corrected_content
    review.reviewed_by = context.user_id
    review.reviewed_at = utc_now()
    review.external_use_ready_at = utc_now() + timedelta(hours=2)
    
    audit = AuditLog(
        tenant_id=context,
        matter_id=review.matter_id,
        user_id=context.user_id,
        action="CORRECT_REVIEW",
        entity_type=review.entity_type,
        entity_id=review.entity_id,
        details={
            "original_content": review.proposed_content,
            "corrected_content": request.corrected_content
        }
    )
    db.add(audit)
    
    await db.commit()
    return {"status": "success", "message": "Review corrected and approved"}
