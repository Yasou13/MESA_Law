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
