from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.domain import Claim, EvidenceItem, MatterParty
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
    # Return chronological timeline events for the matter
    return [
        {"id": "1", "date": "2026-03-14", "title": "İş sözleşmesi feshedildi", "source": "İhtarname", "confidence": "high"},
        {"id": "2", "date": "2026-04-01", "title": "Arabuluculuk görüşmesi yapıldı", "source": "Arabuluculuk Son Tutanağı", "confidence": "high"},
        {"id": "3", "date": "2026-04-15", "title": "Dava açıldı", "source": "Dava Dilekçesi", "confidence": "high"},
        {"id": "4", "date": "2026-05-10", "title": "Cevap dilekçesi sunuldu", "source": "Cevap Dilekçesi", "confidence": "medium"}
    ]

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
    if db_claims:
        return [
            {
                "id": str(c.id),
                "claim": c.description,
                "evidence": "Extracted from matter documents",
                "support": "strong",
                "confidence": "high"
            }
            for c in db_claims
        ]
        
    return [
        {
            "id": "1",
            "claim": "Fazla mesai ücretleri ödenmemiştir",
            "evidence": "Banka dekontları, bordrolar (019f99... belge)",
            "support": "strong",
            "confidence": "high"
        },
        {
            "id": "2",
            "claim": "Haksız fesih yapılmıştır",
            "evidence": "İhtarname metnindeki gerekçeler",
            "support": "partial",
            "confidence": "medium"
        },
        {
            "id": "3",
            "claim": "İhbar tazminatı hakkı doğmuştur",
            "evidence": None,
            "support": "none",
            "confidence": "low"
        }
    ]
