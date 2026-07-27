from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import Claim, EvidenceItem, MatterParty, MatterEvent, ClaimEvidenceLink
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.core.ratelimit import limiter
from fastapi import Request

router = APIRouter()

@router.get("/matters/{matter_id}/parties", operation_id="listMatterParties")
@limiter.limit("100/minute")
async def list_matter_parties(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MatterParty).where(MatterParty.matter_id == matter_id, MatterParty.tenant_id == context.tenant_id))
    parties = result.scalars().all()
    return parties

@router.get("/matters/{matter_id}/claims", operation_id="listClaims")
@limiter.limit("100/minute")
async def list_claims(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Claim).where(Claim.matter_id == matter_id, Claim.tenant_id == context.tenant_id))
    claims = result.scalars().all()
    return claims

@router.get("/matters/{matter_id}/evidence", operation_id="listEvidence")
@limiter.limit("100/minute")
async def list_evidence(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(EvidenceItem).where(EvidenceItem.matter_id == matter_id, EvidenceItem.tenant_id == context.tenant_id))
    evidence = result.scalars().all()
    return evidence

@router.get("/matters/{matter_id}/timeline", operation_id="listTimelineEvents")
@limiter.limit("100/minute")
async def list_timeline_events(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Fetch actual MatterEvents instead of generic documents
    result = await db.execute(select(MatterEvent).where(MatterEvent.matter_id == matter_id, MatterEvent.tenant_id == context.tenant_id))
    db_events = result.scalars().all()
    
    events = []
    for e in db_events:
        events.append({
            "id": f"event_{e.id}",
            "date": e.event_date,
            "title": e.event_type,
            "description": e.description,
            "source": e.source_type,
            "confidence": e.confidence
        })
        
    events.sort(key=lambda x: x["date"] if x["date"] != "N/A" else "0000-00-00", reverse=True)
    return events

@router.get("/matters/{matter_id}/claims-evidence", operation_id="listClaimsWithEvidence")
@limiter.limit("100/minute")
async def list_claims_with_evidence(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    claims_res = await db.execute(select(Claim).where(Claim.matter_id == matter_id, Claim.tenant_id == context.tenant_id))
    db_claims = claims_res.scalars().all()
    
    res = []
    for c in db_claims:
        # Check actual evidence items linked to this claim
        link_stmt = select(EvidenceItem).join(ClaimEvidenceLink, EvidenceItem.id == ClaimEvidenceLink.evidence_id).where(ClaimEvidenceLink.claim_id == c.id)
        ev_res = await db.execute(link_stmt)
        ev_items = ev_res.scalars().all()
        
        ev_desc = ", ".join([e.description for e in ev_items]) if ev_items else "Kanıt eşleşmesi bulunamadı."
        res.append({
            "id": str(c.id),
            "claim": c.description,
            "evidence": ev_desc,
            "support": "strong" if ev_items else "none",
            "confidence": "high" if ev_items else "low"
        })
    return res
