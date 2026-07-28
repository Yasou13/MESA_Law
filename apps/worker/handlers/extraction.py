import logging

from apps.api.core.extraction import get_extraction_adapter
from apps.api.models.parser import ParsedDocument, ParsedPage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        
    # Get all text from chunks
    from apps.api.models.parser import DocumentChunk
    chunks_result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == parsed_doc.document_id).order_by(DocumentChunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()
    full_text = "\n\n".join([c.watermarked_text for c in chunks])
    
    if not full_text.strip():
        # Fallback to pages if chunks aren't available for this legacy doc
        pages_result = await session.execute(
            select(ParsedPage).where(ParsedPage.parsed_document_id == parsed_document_id).order_by(ParsedPage.page_number)
        )
        pages = pages_result.scalars().all()
        full_text = "\n\n".join([p.text_content for p in pages])
    
    if not full_text.strip():
        logger.warning(f"ParsedDocument {parsed_document_id} has no text content")
        return
        
    import hashlib

    from apps.api.models.domain import SourceLocator
    from apps.api.models.review import ExtractionSuggestion, ReviewItem, ReviewState

    adapter = get_extraction_adapter()
    matter_id = parsed_doc.document.matter_id if parsed_doc.document else payload.get("matter_id")
    
    # Generate Idempotency Key Helper
    def generate_idempotency_key(doc_rev_id: str, pipeline_v: str, type_str: str, locator: str) -> str:
        raw = f"{doc_rev_id}_{pipeline_v}_{type_str}_{locator}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    # 1. Extract Parties
    parties_data = await adapter.extract_parties(full_text)
    
    import uuid6
    for pd in parties_data:
        ik = generate_idempotency_key(parsed_doc.revision_id, "1.0.0", "PARTY_SUGGESTION", pd.get("provenance", "unknown_party"))
        
        # Check idempotency
        existing_sugg = await session.execute(select(ExtractionSuggestion).where(ExtractionSuggestion.idempotency_key == ik))
        if existing_sugg.scalars().first():
            logger.info(f"Skipping duplicate PARTY_SUGGESTION {ik}")
            continue

        # Phase 7: Create genuine SourceLocator
        locator = SourceLocator(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            parsed_document_id=parsed_document_id,
            page_number=1, # Default/Fallback
            text_snippet=pd.get("provenance", "Snippet not available"),
            text_hash=hashlib.sha256(str(pd.get("provenance", "")).encode()).hexdigest(),
            parser_version=parsed_doc.parser_used
        )
        session.add(locator)
        await session.flush()

        suggestion = ExtractionSuggestion(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            source_locator_id=locator.id,
            suggestion_type="PARTY_SUGGESTION",
            payload={
                "name": pd["name"],
                "role": pd["role"],
                "type": pd["type"]
            },
            extractor_name="adapter",
            extractor_version="1.0.0",
            prompt_version="1.0",
            parser_version=parsed_doc.parser_used,
            idempotency_key=ik
        )
        session.add(suggestion)
        await session.flush()
        
        review_item = ReviewItem(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            entity_type="party",
            entity_id=f"draft_party_{parsed_doc.id}_{pd['name'].replace(' ', '_')}",
            suggestion_id=suggestion.id,
            proposed_content=suggestion.payload,
            status=ReviewState.PENDING
        )
        session.add(review_item)
        
    # 2. Extract Claims
    claims_data = await adapter.extract_claims(full_text)
    
    for cd in claims_data:
        ik = generate_idempotency_key(parsed_doc.revision_id, "1.0.0", "CLAIM_SUGGESTION", cd.get("provenance", "unknown_claim"))
        existing_sugg = await session.execute(select(ExtractionSuggestion).where(ExtractionSuggestion.idempotency_key == ik))
        if existing_sugg.scalars().first():
            logger.info(f"Skipping duplicate CLAIM_SUGGESTION {ik}")
            continue

        # Phase 7: Create genuine SourceLocator
        locator = SourceLocator(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            parsed_document_id=parsed_document_id,
            page_number=1, # Default/Fallback
            text_snippet=cd.get("provenance", "Snippet not available"),
            text_hash=hashlib.sha256(str(cd.get("provenance", "")).encode()).hexdigest(),
            parser_version=parsed_doc.parser_used
        )
        session.add(locator)
        await session.flush()

        suggestion = ExtractionSuggestion(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            source_locator_id=locator.id,
            suggestion_type="CLAIM_SUGGESTION",
            payload={
                "description": cd["description"],
                "confidence": cd.get("confidence", 1.0)
            },
            extractor_name="adapter",
            extractor_version="1.0.0",
            prompt_version="1.0",
            parser_version=parsed_doc.parser_used,
            confidence_category="high" if cd.get("confidence", 1.0) > 0.8 else "medium",
            idempotency_key=ik
        )
        session.add(suggestion)
        await session.flush()
        
        review_item = ReviewItem(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            entity_type="claim",
            entity_id=f"draft_claim_{uuid6.uuid7()}",
            suggestion_id=suggestion.id,
            proposed_content=suggestion.payload,
            status=ReviewState.PENDING
        )
        session.add(review_item)
            
    # 3. Extract Events (Deadlines)
    events_data = await adapter.extract_events(full_text)
    
    for ed in events_data:
        ik = generate_idempotency_key(parsed_doc.revision_id, "1.0.0", "DEADLINE_TRIGGER_SUGGESTION", ed.get("provenance", "unknown_event"))
        existing_sugg = await session.execute(select(ExtractionSuggestion).where(ExtractionSuggestion.idempotency_key == ik))
        if existing_sugg.scalars().first():
            continue
            
        locator = SourceLocator(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            parsed_document_id=parsed_document_id,
            page_number=1,
            text_snippet=ed.get("provenance", "Snippet not available"),
            text_hash=hashlib.sha256(str(ed.get("provenance", "")).encode()).hexdigest(),
            parser_version=parsed_doc.parser_used
        )
        session.add(locator)
        await session.flush()
        
        suggestion = ExtractionSuggestion(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            source_locator_id=locator.id,
            suggestion_type="DEADLINE_TRIGGER_SUGGESTION",
            payload={
                "trigger_event": ed["trigger_event"],
                "rule_name": ed["rule_name"],
                "offset_days": ed["offset_days"],
                "description": ed["description"]
            },
            extractor_name="adapter",
            extractor_version="1.0.0",
            prompt_version="1.0",
            parser_version=parsed_doc.parser_used,
            idempotency_key=ik
        )
        session.add(suggestion)
        await session.flush()
        
        review_item = ReviewItem(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            entity_type="deadline",
            entity_id=f"draft_deadline_{uuid6.uuid7()}",
            suggestion_id=suggestion.id,
            proposed_content=suggestion.payload,
            status=ReviewState.PENDING
        )
        session.add(review_item)
        
    # 4. Extract Evidence
    evidence_data = await adapter.extract_evidence(full_text)
    
    for ev in evidence_data:
        ik = generate_idempotency_key(parsed_doc.revision_id, "1.0.0", "EVIDENCE_SUGGESTION", ev.get("provenance", "unknown_evidence"))
        existing_sugg = await session.execute(select(ExtractionSuggestion).where(ExtractionSuggestion.idempotency_key == ik))
        if existing_sugg.scalars().first():
            continue
            
        locator = SourceLocator(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            parsed_document_id=parsed_document_id,
            page_number=1,
            text_snippet=ev.get("provenance", "Snippet not available"),
            text_hash=hashlib.sha256(str(ev.get("provenance", "")).encode()).hexdigest(),
            parser_version=parsed_doc.parser_used
        )
        session.add(locator)
        await session.flush()
        
        suggestion = ExtractionSuggestion(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            document_id=parsed_doc.document_id,
            document_revision_id=parsed_doc.revision_id,
            source_locator_id=locator.id,
            suggestion_type="EVIDENCE_SUGGESTION",
            payload={
                "description": ev["description"],
                "relevance": ev["relevance"]
            },
            extractor_name="adapter",
            extractor_version="1.0.0",
            prompt_version="1.0",
            parser_version=parsed_doc.parser_used,
            idempotency_key=ik
        )
        session.add(suggestion)
        await session.flush()
        
        review_item = ReviewItem(
            tenant_id=parsed_doc.tenant_id,
            matter_id=matter_id,
            entity_type="evidence",
            entity_id=f"draft_evidence_{uuid6.uuid7()}",
            suggestion_id=suggestion.id,
            proposed_content=suggestion.payload,
            status=ReviewState.PENDING
        )
        session.add(review_item)

    from apps.api.models.audit import AuditEvent, Notification
    
    # Audit Event
    audit = AuditEvent(
        tenant_id=parsed_doc.tenant_id,
        action="EXTRACTION_COMPLETED",
        entity_type="parsed_document",
        entity_id=parsed_document_id,
        changes={"parties": len(parties_data), "claims": len(claims_data), "events": len(events_data), "evidence": len(evidence_data)}
    )
    session.add(audit)
    
    from apps.api.models.domain import Membership, Role
    
    # Notification (send to firm admins)
    user_res = await session.execute(select(Membership.user_id).where(Membership.firm_id == parsed_doc.tenant_id, Membership.role == Role.FIRM_ADMIN))
    admin_ids = user_res.scalars().all()
    for admin_id in admin_ids:
        notification = Notification(
            tenant_id=parsed_doc.tenant_id,
            user_id=admin_id,
            title="Extraction Complete",
            message=f"Review queue updated for document {parsed_document_id}"
        )
        session.add(notification)

    await session.commit()
    logger.info(f"Extraction completed for ParsedDocument {parsed_document_id}. Added suggestions to ReviewQueue.")
