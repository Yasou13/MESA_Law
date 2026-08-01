from datetime import timedelta

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy, ReviewAccessPolicy
from apps.api.core.utils import utc_now
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.review import AuditLog, ReviewItem, ReviewState
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["reviews"])


class ReviewItemResponse(BaseModel):
    id: str
    matter_id: str
    entity_type: str
    entity_id: str
    proposed_content: dict
    status: str
    suggestion_id: str | None = None


class CorrectReviewRequest(BaseModel):
    corrected_content: dict


@router.get("", response_model=list[ReviewItemResponse])
async def list_draft_reviews(
    matter_id: str | None = None,
    status: str | None = None,
    entity_type: str | None = None,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if matter_id:
        await MatterAccessPolicy.can_read(context, db, matter_id)
    else:
        MatterAccessPolicy.can_list(context)

    query = select(ReviewItem).where(ReviewItem.tenant_id == context.tenant_id)

    if matter_id:
        query = query.where(ReviewItem.matter_id == matter_id)
    else:
        from apps.api.models.domain import MatterMember

        query = query.join(
            MatterMember, ReviewItem.matter_id == MatterMember.matter_id
        ).where(
            MatterMember.user_id == context.principal_id,
            MatterMember.tenant_id == context.tenant_id,
        )

    if status:
        query = query.where(ReviewItem.status == ReviewState(status))

    if entity_type:
        query = query.where(ReviewItem.entity_type == entity_type)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{review_id}/approve")
async def approve_review(
    review_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id, ReviewItem.tenant_id == context.tenant_id
        )
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    await ReviewAccessPolicy.can_approve(context, db, review.matter_id)

    if review.status not in (ReviewState.PENDING, ReviewState.IN_REVIEW):
        raise HTTPException(
            status_code=400, detail="Item is not in a valid state for approval"
        )

    review.status = ReviewState.APPROVED_PENDING_PUBLICATION
    review.reviewed_by = context.principal_id
    review.reviewed_at = utc_now()

    # Solo mode policy: cooling-off period of 2 hours for external use
    review.external_use_ready_at = utc_now() + timedelta(hours=2)

    from apps.api.models.queue import Job

    job = Job(
        type="PUBLISH_REVIEW",
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        requested_by=context.principal_id,
        idempotency_key=f"publish:{review.id}:{review.version_id}",
        payload={"review_id": review_id, "matter_id": review.matter_id},
    )
    db.add(job)

    # Create immutable audit log
    audit = AuditLog(
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        user_id=context.principal_id,
        action="APPROVE_REVIEW",
        entity_type=review.entity_type,
        entity_id=review.entity_id,
        details={"original_content": review.proposed_content},
    )
    db.add(audit)

    await db.commit()
    return {
        "status": "success",
        "message": "Review approved with 2-hour cooling-off period for external use",
    }


@router.post("/{review_id}/reject")
async def reject_review(
    review_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id, ReviewItem.tenant_id == context.tenant_id
        )
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    await ReviewAccessPolicy.can_approve(context, db, review.matter_id)

    if review.status not in (ReviewState.PENDING, ReviewState.IN_REVIEW):
        raise HTTPException(
            status_code=400, detail="Item is not in a valid state for rejection"
        )

    review.status = ReviewState.REJECTED
    review.reviewed_by = context.principal_id
    review.reviewed_at = utc_now()

    audit = AuditLog(
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        user_id=context.principal_id,
        action="REJECT_REVIEW",
        entity_type=review.entity_type,
        entity_id=review.entity_id,
        details={"original_content": review.proposed_content},
    )
    db.add(audit)

    await db.commit()
    return {"status": "success", "message": "Review rejected"}


@router.post("/{review_id}/correct")
async def correct_review(
    review_id: str,
    request: CorrectReviewRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id, ReviewItem.tenant_id == context.tenant_id
        )
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    await ReviewAccessPolicy.can_approve(context, db, review.matter_id)

    if review.status not in (ReviewState.PENDING, ReviewState.IN_REVIEW):
        raise HTTPException(
            status_code=400, detail="Item is not in a valid state for correction"
        )

    review.status = ReviewState.APPROVED_PENDING_PUBLICATION
    review.corrected_content = request.corrected_content
    review.reviewed_by = context.principal_id
    review.reviewed_at = utc_now()
    review.external_use_ready_at = utc_now() + timedelta(hours=2)

    from apps.api.models.queue import Job

    job = Job(
        type="PUBLISH_REVIEW",
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        requested_by=context.principal_id,
        idempotency_key=f"publish:{review.id}:{review.version_id}",
        payload={"review_id": review_id, "matter_id": review.matter_id},
    )
    db.add(job)

    audit = AuditLog(
        tenant_id=context.tenant_id,
        matter_id=review.matter_id,
        user_id=context.principal_id,
        action="CORRECT_REVIEW",
        entity_type=review.entity_type,
        entity_id=review.entity_id,
        details={
            "original_content": review.proposed_content,
            "corrected_content": request.corrected_content,
        },
    )
    db.add(audit)

    await db.commit()
    return {"status": "success", "message": "Review corrected and approved"}
