from datetime import timedelta

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy, ReviewAccessPolicy
from apps.api.core.utils import utc_now
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import MatterMember
from apps.api.models.queue import Job
from apps.api.models.review import (
    AuditLog,
    ExtractionSuggestion,
    ReviewItem,
    ReviewState,
)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["reviews"])


class ReviewItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    entity_type: str
    entity_id: str
    proposed_content: dict
    corrected_content: dict | None = None
    status: ReviewState
    suggestion_id: str | None = None
    decision_reason: str | None = None
    version_id: int


class ReviewMutationRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str | None = Field(default=None, min_length=3, max_length=1000)


class RejectReviewRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=1000)


class CorrectReviewRequest(RejectReviewRequest):
    corrected_content: dict = Field(min_length=1)


class ReviewMutationResponse(BaseModel):
    id: str
    status: ReviewState
    version_id: int
    publication_job_id: str | None = None


async def _load_review(
    db: AsyncSession, context: RequestContext, review_id: str
) -> ReviewItem:
    review = await db.scalar(
        select(ReviewItem).where(
            ReviewItem.id == review_id,
            ReviewItem.tenant_id == context.tenant_id,
        )
    )
    if review is None:
        raise HTTPException(status_code=404, detail="Review item not found")
    await ReviewAccessPolicy.can_approve(context, db, review.matter_id)
    return review


async def _transition_proposal(
    db: AsyncSession,
    *,
    review: ReviewItem,
    expected_version: int,
    target: ReviewState,
    principal_id: str,
    reason: str | None,
    corrected_content: dict | None = None,
) -> ReviewItem:
    if review.version_id != expected_version:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "STALE_REVIEW_VERSION",
                "expected_version": expected_version,
                "current_version": review.version_id,
            },
        )
    if review.status != ReviewState.PROPOSED:
        raise HTTPException(
            status_code=409,
            detail={"code": "INVALID_REVIEW_STATE", "state": review.status.value},
        )

    now = utc_now()
    values = {
        "status": target,
        "reviewed_by": principal_id,
        "reviewed_at": now,
        "decision_reason": reason,
        "corrected_content": corrected_content,
        "external_use_ready_at": (
            now + timedelta(hours=2) if target != ReviewState.REJECTED else None
        ),
        "version_id": ReviewItem.version_id + 1,
        "updated_at": now,
    }
    result = await db.execute(
        update(ReviewItem)
        .where(
            ReviewItem.id == review.id,
            ReviewItem.tenant_id == review.tenant_id,
            ReviewItem.status == ReviewState.PROPOSED,
            ReviewItem.version_id == expected_version,
        )
        .values(**values)
        .returning(ReviewItem)
    )
    updated = result.scalar_one_or_none()
    if updated is None:
        raise HTTPException(status_code=409, detail={"code": "STALE_REVIEW_VERSION"})
    if updated.suggestion_id:
        await db.execute(
            update(ExtractionSuggestion)
            .where(
                ExtractionSuggestion.id == updated.suggestion_id,
                ExtractionSuggestion.tenant_id == updated.tenant_id,
            )
            .values(review_state=target.value, updated_at=now)
        )
    return updated


@router.get("", response_model=list[ReviewItemResponse], operation_id="listReviews")
async def list_draft_reviews(
    matter_id: str | None = None,
    status: ReviewState | None = None,
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
        query = query.join(
            MatterMember, ReviewItem.matter_id == MatterMember.matter_id
        ).where(
            MatterMember.user_id == context.principal_id,
            MatterMember.tenant_id == context.tenant_id,
        )
    if status:
        query = query.where(ReviewItem.status == status)
    if entity_type:
        query = query.where(ReviewItem.entity_type == entity_type)
    return (await db.execute(query.order_by(ReviewItem.created_at))).scalars().all()


@router.post(
    "/{review_id}/approve",
    response_model=ReviewMutationResponse,
    operation_id="approveReview",
)
async def approve_review(
    review_id: str,
    request: ReviewMutationRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    review = await _load_review(db, context, review_id)
    updated = await _transition_proposal(
        db,
        review=review,
        expected_version=request.expected_version,
        target=ReviewState.APPROVED,
        principal_id=context.principal_id,
        reason=request.reason,
    )
    job = Job(
        type="PUBLISH_REVIEW",
        tenant_id=context.tenant_id,
        matter_id=updated.matter_id,
        requested_by=context.principal_id,
        idempotency_key=f"publish:{updated.id}:{updated.version_id}",
        payload={"review_id": updated.id, "matter_id": updated.matter_id},
    )
    db.add(job)
    db.add(
        AuditLog(
            tenant_id=context.tenant_id,
            matter_id=updated.matter_id,
            user_id=context.principal_id,
            action="APPROVE_REVIEW",
            entity_type=updated.entity_type,
            entity_id=updated.entity_id,
            details={
                "before": review.proposed_content,
                "after": review.proposed_content,
                "reason": request.reason,
                "review_version": updated.version_id,
            },
        )
    )
    await db.commit()
    return ReviewMutationResponse(
        id=updated.id,
        status=updated.status,
        version_id=updated.version_id,
        publication_job_id=job.id,
    )


@router.post(
    "/{review_id}/reject",
    response_model=ReviewMutationResponse,
    operation_id="rejectReview",
)
async def reject_review(
    review_id: str,
    request: RejectReviewRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    review = await _load_review(db, context, review_id)
    updated = await _transition_proposal(
        db,
        review=review,
        expected_version=request.expected_version,
        target=ReviewState.REJECTED,
        principal_id=context.principal_id,
        reason=request.reason,
    )
    db.add(
        AuditLog(
            tenant_id=context.tenant_id,
            matter_id=updated.matter_id,
            user_id=context.principal_id,
            action="REJECT_REVIEW",
            entity_type=updated.entity_type,
            entity_id=updated.entity_id,
            details={
                "before": review.proposed_content,
                "after": None,
                "reason": request.reason,
                "review_version": updated.version_id,
            },
        )
    )
    await db.commit()
    return ReviewMutationResponse(
        id=updated.id, status=updated.status, version_id=updated.version_id
    )


@router.post(
    "/{review_id}/correct",
    response_model=ReviewMutationResponse,
    operation_id="correctReview",
)
async def correct_review(
    review_id: str,
    request: CorrectReviewRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    review = await _load_review(db, context, review_id)
    updated = await _transition_proposal(
        db,
        review=review,
        expected_version=request.expected_version,
        target=ReviewState.CORRECTED,
        principal_id=context.principal_id,
        reason=request.reason,
        corrected_content=request.corrected_content,
    )
    job = Job(
        type="PUBLISH_REVIEW",
        tenant_id=context.tenant_id,
        matter_id=updated.matter_id,
        requested_by=context.principal_id,
        idempotency_key=f"publish:{updated.id}:{updated.version_id}",
        payload={"review_id": updated.id, "matter_id": updated.matter_id},
    )
    db.add(job)
    db.add(
        AuditLog(
            tenant_id=context.tenant_id,
            matter_id=updated.matter_id,
            user_id=context.principal_id,
            action="CORRECT_REVIEW",
            entity_type=updated.entity_type,
            entity_id=updated.entity_id,
            details={
                "before": review.proposed_content,
                "after": request.corrected_content,
                "reason": request.reason,
                "review_version": updated.version_id,
            },
        )
    )
    await db.commit()
    return ReviewMutationResponse(
        id=updated.id,
        status=updated.status,
        version_id=updated.version_id,
        publication_job_id=job.id,
    )
