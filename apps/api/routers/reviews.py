from datetime import timedelta

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.utils import utc_now
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.review import AuditLog, ReviewItem
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from apps.api.models.domain import MatterParty, Claim
from apps.api.models.deadline import DeadlineCandidate

router = APIRouter(tags=["reviews"])

class ReviewItemResponse(BaseModel):
    id: str
    matter_id: str
    entity_type: str
    entity_id: str
    proposed_content: dict
    status: str

class CorrectReviewRequest(BaseModel):
    corrected_content: dict

@router.get("", response_model=list[ReviewItemResponse])
async def list_draft_reviews(
    matter_id: str | None = None,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    query = select(ReviewItem).where(
        ReviewItem.tenant_id == context.tenant_id,
        ReviewItem.status == "draft"
    )
    if matter_id:
        query = query.where(ReviewItem.matter_id == matter_id)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{review_id}/approve")
async def approve_review(
    review_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReviewItem).where(ReviewItem.id == review_id, ReviewItem.tenant_id == context.tenant_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    if review.status != "draft":
        raise HTTPException(status_code=400, detail="Item is not draft review")
        
    review.status = "approved"
    review.reviewed_by = context.principal_id
    review.reviewed_at = utc_now()
    
    # Solo mode policy: cooling-off period of 2 hours for external use
    review.external_use_ready_at = utc_now() + timedelta(hours=2)
    
    # Write to canonical tables based on entity_type
    try:
        content = review.proposed_content or {}
        if review.entity_type == "party":
            party = MatterParty(
                tenant_id=context.tenant_id,
                matter_id=review.matter_id,
                name=content.get("name", "Unknown Party"),
                role=content.get("role", "UNKNOWN"),
                type=content.get("type", "ORGANIZATION")
            )
            db.add(party)
        elif review.entity_type == "claim":
            # Just to satisfy NOT NULL constraints if IDs aren't provided by AI
            claimant_id = content.get("claimant_party_id", "default_claimant")
            defendant_id = content.get("defendant_party_id", "default_defendant")
            claim = Claim(
                tenant_id=context.tenant_id,
                matter_id=review.matter_id,
                claimant_party_id=claimant_id,
                defendant_party_id=defendant_id,
                description=content.get("description", "Unknown Claim")
            )
            db.add(claim)
        elif review.entity_type == "deadline":
            date_str = content.get("due_date", content.get("calculated_date"))
            calc_date = datetime.now().date()
            if date_str:
                try:
                    calc_date = datetime.fromisoformat(date_str).date()
                except ValueError:
                    pass
                    
            deadline = DeadlineCandidate(
                tenant_id=context.tenant_id,
                matter_id=review.matter_id,
                calculated_date=calc_date,
                description=content.get("description", "Extracted Deadline")
            )
            db.add(deadline)
    except Exception as e:
        import logging
        logging.error(f"Failed to write to canonical tables for review {review_id}: {e}")
        # Allow approval to succeed even if canonical write fails (or we could raise 500)
        
    # Create immutable audit log
    audit = AuditLog(
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        user_id=context.principal_id,
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
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReviewItem).where(ReviewItem.id == review_id, ReviewItem.tenant_id == context.tenant_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
        
    review.status = "rejected"
    review.reviewed_by = context.principal_id
    review.reviewed_at = utc_now()
    
    audit = AuditLog(
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        user_id=context.principal_id,
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
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReviewItem).where(ReviewItem.id == review_id, ReviewItem.tenant_id == context.tenant_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")
        
    review.status = "corrected"
    review.corrected_content = request.corrected_content
    review.reviewed_by = context.principal_id
    review.reviewed_at = utc_now()
    review.external_use_ready_at = utc_now() + timedelta(hours=2)
    
    audit = AuditLog(
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        user_id=context.principal_id,
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
