import logging

from apps.api.models.domain import Claim, LegalAssertion, MatterParty
from apps.api.models.draft import Draft
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.draft")

async def handle_generate_draft(payload: dict, session: AsyncSession):
    tenant_id = payload.get("tenant_id")
    matter_id = payload.get("matter_id")
    template_name = payload.get("template_name", "default")
    
    if not all([tenant_id, matter_id]):
        logger.error("Missing tenant_id or matter_id in GENERATE_DRAFT")
        return
        
    logger.info(f"Generating draft for matter {matter_id} using template {template_name}")
    
    # Fetch Canonical Data
    parties_res = await session.execute(
        select(MatterParty).where(MatterParty.matter_id == matter_id)
    )
    parties = parties_res.scalars().all()
    
    claims_res = await session.execute(
        select(Claim).where(Claim.matter_id == matter_id)
    )
    claims = claims_res.scalars().all()
    
    assertions_res = await session.execute(
        select(LegalAssertion).where(LegalAssertion.matter_id == matter_id)
    )
    assertions = assertions_res.scalars().all()
    
    # Build Content Mock
    content_lines = [f"<h1>Dilekçe Taslağı: {template_name}</h1>"]
    content_lines.append("<h2>Taraflar</h2><ul>")
    for p in parties:
        content_lines.append(f"<li>{p.role}: {p.name} ({p.type})</li>")
    content_lines.append("</ul>")
    
    content_lines.append("<h2>Talepler (Claims)</h2><ul>")
    for c in claims:
        content_lines.append(f"<li>{c.description}</li>")
    content_lines.append("</ul>")
    
    content_lines.append("<h2>Hukuki Dayanaklar (Legal Assertions)</h2><ul>")
    for a in assertions:
        content_lines.append(f"<li>{a.assertion_text}</li>")
    content_lines.append("</ul>")
    
    final_content = "".join(content_lines)
    
    # Mock PDF generation S3 path
    mock_s3_pdf_url = f"s3://mesa-law-drafts/{tenant_id}/{matter_id}/draft.pdf"
    logger.info(f"Mock S3 PDF generated at {mock_s3_pdf_url}")
    
    # Save to Draft model
    draft = Draft(
        tenant_id=tenant_id,
        matter_id=matter_id,
        title=f"Otomatik Taslak - {template_name}",
        content=final_content,
        version=1
    )
    session.add(draft)
    await session.commit()
    logger.info(f"Draft generated and saved for matter {matter_id}")
