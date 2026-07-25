import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.parser import ParsedDocument, ParsedPage
from apps.api.models.domain import MatterParty, Claim
from apps.api.core.extraction import get_extraction_adapter

logger = logging.getLogger("worker.extraction")

async def handle_extract_legal_data(payload: dict, session: AsyncSession):
    parsed_document_id = payload.get("parsed_document_id")
    if not parsed_document_id:
        logger.error("Missing parsed_document_id in payload")
        return
        
    parsed_doc = await session.get(ParsedDocument, parsed_document_id)
    if not parsed_doc:
        logger.error(f"ParsedDocument {parsed_document_id} not found")
        return
        
    # Get all text from document
    pages_result = await session.execute(
        select(ParsedPage).where(ParsedPage.parsed_document_id == parsed_document_id).order_by(ParsedPage.page_number)
    )
    pages = pages_result.scalars().all()
    full_text = "\n\n".join([p.text_content for p in pages])
    
    if not full_text.strip():
        logger.warning(f"ParsedDocument {parsed_document_id} has no text content")
        return
        
    adapter = get_extraction_adapter()
    
    # 1. Extract Parties
    parties_data = await adapter.extract_parties(full_text)
    party_map = {}
    
    for pd in parties_data:
        party = MatterParty(
            tenant_id=parsed_doc.tenant_id,
            matter_id=parsed_doc.document.matter_id if parsed_doc.document else payload.get("matter_id"), # fallback
            name=pd["name"],
            role=pd["role"],
            type=pd["type"]
        )
        session.add(party)
        party_map[pd["role"]] = party
        
    await session.flush()
    
    # 2. Extract Claims
    claims_data = await adapter.extract_claims(full_text)
    
    claimant = party_map.get("PLAINTIFF") or party_map.get("CLAIMANT")
    defendant = party_map.get("DEFENDANT")
    
    if claimant and defendant:
        for cd in claims_data:
            claim = Claim(
                tenant_id=parsed_doc.tenant_id,
                matter_id=parsed_doc.document.matter_id if parsed_doc.document else payload.get("matter_id"),
                claimant_party_id=claimant.id,
                defendant_party_id=defendant.id,
                description=cd["description"],
                status="suggested",
                review_status="pending_review"
            )
            session.add(claim)
            
    await session.commit()
    logger.info(f"Extraction completed for ParsedDocument {parsed_document_id}")
