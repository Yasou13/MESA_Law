from datetime import datetime

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy
from apps.api.core.ratelimit import limiter
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import (
    Claim,
    ClaimEvidenceLink,
    EvidenceItem,
    MatterEvent,
)
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    claimant_party_id: str
    defendant_party_id: str
    description: str
    status: str
    review_status: str
    source_locator_id: str | None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    document_id: str | None
    description: str
    review_status: str
    source_locator_id: str | None


class TimelineEventResponse(BaseModel):
    id: str
    date: datetime
    title: str
    description: str | None
    source: str
    confidence: str


class ClaimEvidenceResponse(BaseModel):
    id: str
    claim: str
    evidence: str
    support: str
    confidence: str


@router.get(
    "/matters/{matter_id}/claims",
    operation_id="listClaims",
    response_model=list[ClaimResponse],
)
@limiter.limit("100/minute")
async def list_claims(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    result = await db.execute(
        select(Claim).where(
            Claim.matter_id == matter_id, Claim.tenant_id == context.tenant_id
        )
    )
    claims = result.scalars().all()
    return claims


@router.get(
    "/matters/{matter_id}/evidence",
    operation_id="listEvidence",
    response_model=list[EvidenceResponse],
)
@limiter.limit("100/minute")
async def list_evidence(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    result = await db.execute(
        select(EvidenceItem).where(
            EvidenceItem.matter_id == matter_id,
            EvidenceItem.tenant_id == context.tenant_id,
        )
    )
    evidence = result.scalars().all()
    return evidence


@router.get(
    "/matters/{matter_id}/timeline",
    operation_id="listTimelineEvents",
    response_model=list[TimelineEventResponse],
)
@limiter.limit("100/minute")
async def list_timeline_events(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    # Fetch actual MatterEvents instead of generic documents
    result = await db.execute(
        select(MatterEvent).where(
            MatterEvent.matter_id == matter_id,
            MatterEvent.tenant_id == context.tenant_id,
        )
    )
    db_events = result.scalars().all()

    events: list[TimelineEventResponse] = []
    for e in db_events:
        events.append(
            TimelineEventResponse(
                id=f"event_{e.id}",
                date=e.event_date.isoformat(),
                title=e.event_type,
                description=e.description,
                source=e.source_type,
                confidence=e.confidence,
            )
        )

    events.sort(key=lambda event: event.date, reverse=True)
    return events


@router.get(
    "/matters/{matter_id}/claims-evidence",
    operation_id="listClaimsWithEvidence",
    response_model=list[ClaimEvidenceResponse],
)
@limiter.limit("100/minute")
async def list_claims_with_evidence(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    claims_res = await db.execute(
        select(Claim).where(
            Claim.matter_id == matter_id, Claim.tenant_id == context.tenant_id
        )
    )
    db_claims = claims_res.scalars().all()

    res = []
    for c in db_claims:
        # Check actual evidence items linked to this claim
        link_stmt = (
            select(EvidenceItem)
            .join(ClaimEvidenceLink, EvidenceItem.id == ClaimEvidenceLink.evidence_id)
            .where(ClaimEvidenceLink.claim_id == c.id)
        )
        ev_res = await db.execute(link_stmt)
        ev_items = ev_res.scalars().all()

        ev_desc = (
            ", ".join([e.description for e in ev_items])
            if ev_items
            else "Kanıt eşleşmesi bulunamadı."
        )
        res.append(
            {
                "id": str(c.id),
                "claim": c.description,
                "evidence": ev_desc,
                "support": "strong" if ev_items else "none",
                "confidence": "high" if ev_items else "low",
            }
        )
    return res
