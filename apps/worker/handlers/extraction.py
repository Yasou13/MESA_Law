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
        
    import json
    from apps.api.models.domain import ReviewItem

    adapter = get_extraction_adapter()
    matter_id = parsed_doc.document.matter_id if parsed_doc.document else payload.get("matter_id")
    
    # 1. Extract Parties
    parties_data = await adapter.extract_parties(full_text)
    
    for pd in parties_data:
        review_item = ReviewItem(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            item_type="party",
            payload=json.dumps({
                "name": pd["name"],
                "role": pd["role"],
                "type": pd["type"],
                "source_document_id": parsed_doc.document_id
            }),
            status="pending"
        )
        session.add(review_item)
        
    await session.flush()
    
    # 2. Extract Claims
    claims_data = await adapter.extract_claims(full_text)
    
    for cd in claims_data:
        review_item = ReviewItem(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            item_type="claim",
            payload=json.dumps({
                "description": cd["description"],
                "confidence": cd.get("confidence", 1.0),
                "source_document_id": parsed_doc.document_id
            }),
            status="pending"
        )
        session.add(review_item)
            
    await session.commit()
    logger.info(f"Extraction completed for ParsedDocument {parsed_document_id}. Added suggestions to ReviewItems.")
