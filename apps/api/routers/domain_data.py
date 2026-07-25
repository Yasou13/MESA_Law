from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import Claim, EvidenceItem, MatterParty
from apps.api.models.document import Document
from apps.api.models.deadline import ApprovedDeadline
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
    # Construct chronological timeline from real documents and deadlines
    doc_res = await db.execute(select(Document).where(Document.matter_id == matter_id, Document.tenant_id == context.tenant_id))
    docs = doc_res.scalars().all()
    
    dl_res = await db.execute(select(ApprovedDeadline).where(ApprovedDeadline.matter_id == matter_id, ApprovedDeadline.tenant_id == context.tenant_id))
    deadlines = dl_res.scalars().all()
    
    events = []
    for d in docs:
        events.append({
            "id": f"doc_{d.id}",
            "date": d.created_at.strftime("%Y-%m-%d") if d.created_at else "N/A",
            "title": f"Belge Yüklendi: {d.title}",
            "source": "Sistem (Belge Yükleme)",
            "confidence": "high"
        })
    for dl in deadlines:
        events.append({
            "id": f"dl_{dl.id}",
            "date": dl.approved_date.strftime("%Y-%m-%d") if dl.approved_date else "N/A",
            "title": f"Kesinleşmiş Süre: {dl.description}",
            "source": "Takvim / Mevzuat",
            "confidence": "high"
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
        # Check if there are evidence items linking to this claim's matter
        ev_res = await db.execute(select(EvidenceItem).where(EvidenceItem.matter_id == matter_id, EvidenceItem.tenant_id == context.tenant_id))
        ev_items = ev_res.scalars().all()
        ev_desc = ", ".join([e.description for e in ev_items]) if ev_items else "Belgelerden inceleniyor"
        res.append({
            "id": str(c.id),
            "claim": c.description,
            "evidence": ev_desc,
            "support": "strong" if ev_items else "partial",
            "confidence": "high" if ev_items else "medium"
        })
    return res
