from datetime import datetime, timedelta

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy, ReviewAccessPolicy
from apps.api.core.utils import utc_now
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.document import Document
from apps.api.models.domain import MatterMember, SourceLocator
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


class ReviewSuggestionContext(BaseModel):
    id: str
    suggestion_type: str
    extractor_name: str
    extractor_version: str
    parser_version: str
    confidence_category: str


class ReviewSourceContext(BaseModel):
    document_id: str
    document_title: str
    revision_id: str
    page_number: int | None = None
    chunk_id: str | None = None
    text_start: int | None = None
    text_end: int | None = None
    bbox: dict[str, float] | None = None
    evidence_text: str | None = None
    evidence_sha256: str | None = None
    parser_version: str | None = None
    extraction_version: str | None = None
    provenance_state: str


class ReviewAuditEntry(BaseModel):
    id: str
    action: str
    user_id: str
    created_at: datetime
    details: dict


class ReviewContextResponse(BaseModel):
    review: ReviewItemResponse
    suggestion: ReviewSuggestionContext | None = None
    source: ReviewSourceContext | None = None
    history: list[ReviewAuditEntry] = Field(default_factory=list)


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


async def _load_review_for_read(
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
    await MatterAccessPolicy.can_read(context, db, review.matter_id)
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


@router.get(
    "/{review_id}/context",
    response_model=ReviewContextResponse,
    operation_id="getReviewContext",
)
async def get_review_context(
    review_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    review = await _load_review_for_read(db, context, review_id)
    suggestion = None
    source = None
    if review.suggestion_id:
        suggestion = await db.scalar(
            select(ExtractionSuggestion).where(
                ExtractionSuggestion.id == review.suggestion_id,
                ExtractionSuggestion.tenant_id == context.tenant_id,
                ExtractionSuggestion.matter_id == review.matter_id,
            )
        )

    if suggestion and suggestion.source_locator_id:
        source_row = (
            await db.execute(
                select(SourceLocator, Document)
                .join(Document, SourceLocator.document_id == Document.id)
                .where(
                    SourceLocator.id == suggestion.source_locator_id,
                    SourceLocator.tenant_id == context.tenant_id,
                    SourceLocator.matter_id == review.matter_id,
                    SourceLocator.document_id == suggestion.document_id,
                    SourceLocator.document_revision_id
                    == suggestion.document_revision_id,
                    Document.tenant_id == context.tenant_id,
                    Document.matter_id == review.matter_id,
                )
            )
        ).one_or_none()
        if source_row:
            locator, document = source_row
            bbox_values = (
                locator.bbox_x0,
                locator.bbox_y0,
                locator.bbox_x1,
                locator.bbox_y1,
            )
            bbox = None
            if all(value is not None for value in bbox_values):
                bbox = {
                    "x0": locator.bbox_x0,
                    "y0": locator.bbox_y0,
                    "x1": locator.bbox_x1,
                    "y1": locator.bbox_y1,
                }
            source = ReviewSourceContext(
                document_id=document.id,
                document_title=document.title,
                revision_id=suggestion.document_revision_id,
                page_number=locator.page_number,
                chunk_id=locator.chunk_id,
                text_start=locator.character_start,
                text_end=locator.character_end,
                bbox=bbox,
                evidence_text=locator.evidence_text or locator.text_snippet,
                evidence_sha256=locator.evidence_sha256 or locator.text_hash,
                parser_version=locator.parser_version,
                extraction_version=locator.extraction_version,
                provenance_state=locator.provenance_state,
            )

    history = (
        (
            await db.execute(
                select(AuditLog)
                .where(
                    AuditLog.tenant_id == context.tenant_id,
                    AuditLog.matter_id == review.matter_id,
                    AuditLog.entity_type == review.entity_type,
                    AuditLog.entity_id == review.entity_id,
                    AuditLog.action.in_(
                        ("APPROVE_REVIEW", "CORRECT_REVIEW", "REJECT_REVIEW")
                    ),
                )
                .order_by(AuditLog.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    return ReviewContextResponse(
        review=ReviewItemResponse.model_validate(review),
        suggestion=(
            ReviewSuggestionContext(
                id=suggestion.id,
                suggestion_type=suggestion.suggestion_type,
                extractor_name=suggestion.extractor_name,
                extractor_version=suggestion.extractor_version,
                parser_version=suggestion.parser_version,
                confidence_category=suggestion.confidence_category,
            )
            if suggestion
            else None
        ),
        source=source,
        history=[
            ReviewAuditEntry(
                id=entry.id,
                action=entry.action,
                user_id=entry.user_id,
                created_at=entry.created_at,
                details=entry.details,
            )
            for entry in history
        ],
    )


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
