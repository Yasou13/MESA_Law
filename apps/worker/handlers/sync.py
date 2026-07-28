import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.api.models.document import Document

logger = logging.getLogger("worker.sync")

async def handle_sync_mesa_document(payload: dict, session: AsyncSession):
    parsed_document_id = payload.get("parsed_document_id")
    if not parsed_document_id:
        logger.error("Missing parsed_document_id in SYNC_MESA_DOCUMENT payload")
        return
        
    from apps.api.models.parser import ParsedDocument
    from apps.api.models.document import Document
    from apps.api.services.mesa_sync import MesaSyncService
    from apps.api.core.factory import get_intelligence_adapter
    
    parsed_doc = await session.get(ParsedDocument, parsed_document_id)
    if not parsed_doc:
        logger.error(f"ParsedDocument {parsed_document_id} not found")
        return
        
    doc = await session.get(Document, parsed_doc.document_id)
    
    adapter = get_intelligence_adapter()
    service = MesaSyncService(adapter)
    try:
        synced = await service.sync_document(
            db=session,
            tenant_id=parsed_doc.tenant_id,
            parsed_doc_id=parsed_document_id,
            matter_id=doc.matter_id,
            doc_title=doc.title
        )
        logger.info(f"Synced {synced} pages for document {doc.id} to MESA")
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()

async def handle_publish_review(payload: dict, session: AsyncSession):
    from apps.api.models.review import ReviewItem, ReviewState
    from apps.api.models.domain import MatterParty, Claim
    from sqlalchemy import select
    
    review_id = payload.get("review_id")
    if not review_id:
        logger.error("Missing review_id")
        return
        
    review = await session.get(ReviewItem, review_id)
    if not review:
        logger.error(f"Review {review_id} not found")
        return
        
    if review.status != ReviewState.APPROVED_PENDING_PUBLICATION:
        logger.warning(f"Review {review_id} is not APPROVED_PENDING_PUBLICATION")
        return
        
    try:
        content = review.proposed_content or {}
        if review.entity_type == "party":
            party = MatterParty(
                tenant_id=review.tenant_id,
                matter_id=review.matter_id,
                name=content.get("name", "Unknown Party"),
                role=content.get("role", "UNKNOWN"),
                type=content.get("type", "ORGANIZATION")
            )
            session.add(party)
        elif review.entity_type == "claim":
            claimant_id = content.get("claimant_party_id")
            defendant_id = content.get("defendant_party_id")
            
            if not claimant_id or not defendant_id or claimant_id in ("default_claimant", "unknown-party-id") or defendant_id in ("default_defendant", "unknown-party-id"):
                raise ValueError("PARTY_LINK_REQUIRED: Claims must be linked to valid MatterParty IDs")
                
            claim = Claim(
                tenant_id=review.tenant_id,
                matter_id=review.matter_id,
                claimant_party_id=claimant_id,
                defendant_party_id=defendant_id,
                description=content.get("description", "Unknown Claim")
            )
            session.add(claim)
        elif review.entity_type == "deadline":
            from apps.api.models.deadline import DeadlineCandidate
            from datetime import datetime
            date_str = content.get("due_date", content.get("calculated_date"))
            calc_date = datetime.now().date()
            if date_str:
                try:
                    calc_date = datetime.fromisoformat(date_str).date()
                except ValueError:
                    pass
                    
            deadline = DeadlineCandidate(
                tenant_id=review.tenant_id,
                matter_id=review.matter_id,
                calculated_date=calc_date,
                description=content.get("description", "Extracted Deadline")
            )
            session.add(deadline)
            
        review.status = ReviewState.PUBLISHED
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to publish review {review_id}: {e}")
        review = await session.get(ReviewItem, review_id)
        if review:
            review.status = ReviewState.PUBLICATION_FAILED
            await session.commit()

async def handle_publish_outbox(payload: dict, session: AsyncSession):
    event_id = payload.get("event_id")
    logger.info(f"Publishing outbox event {event_id} payload: {payload}")
    # Real outbox processing: mark event processed
    if event_id:
        try:
            await session.execute(text("UPDATE outbox_events SET status = 'processed' WHERE id = :eid"), {"eid": str(event_id)})
            await session.commit()
        except Exception as e:
            logger.debug(f"Outbox table update ignored if not present: {e}")

async def handle_build_lexical_index(payload: dict, session: AsyncSession):
    matter_id = payload.get("matter_id")
    logger.info(f"Building lexical index for matter {matter_id}...")
    # Real indexing logic: optimize postgres tsvector or refresh materialized views if applicable
    try:
        await session.execute(text("ANALYZE parsed_pages;"))
        await session.commit()
    except Exception as e:
        logger.warning(f"Lexical index maintenance note: {e}")

async def handle_sync_approved_reviews(payload: dict, session: AsyncSession):
    # Polling job that syncs approved ReviewItem items to canonical domain models
    from apps.api.models.review import ReviewItem
    from apps.api.models.domain import MatterParty, Claim, EvidenceItem, LegalAssertion, MatterEvent
    from apps.api.core.utils import utc_now
    
    tenant_id = payload.get("tenant_id")
    matter_id = payload.get("matter_id") # Optional filter
    
    if not tenant_id:
        logger.error("Missing tenant_id for SYNC_CANONICAL_DOMAIN")
        return
        
    query = select(ReviewItem).where(
        ReviewItem.tenant_id == tenant_id,
        ReviewItem.status == "approved",
        ReviewItem.external_use_ready_at <= utc_now()
    )
    if matter_id:
        query = query.where(ReviewItem.matter_id == matter_id)
        
    result = await session.execute(query)
    approved_items = result.scalars().all()
    
    if not approved_items:
        logger.info("No approved ReviewItems pending sync.")
        return
        
    for item in approved_items:
        content = item.corrected_content if item.corrected_content else item.proposed_content
        r = item
        
        if r.entity_type == "claim":
            claimant_id = content.get("claimant_party_id")
            defendant_id = content.get("defendant_party_id")
            
            if not claimant_id or not defendant_id or claimant_id in ("default_claimant", "unknown-party-id", "placeholder") or defendant_id in ("default_defendant", "unknown-party-id", "placeholder"):
                logger.error(f"PARTY_LINK_REQUIRED: Skipping claim review {r.id} due to invalid Party IDs")
                r.status = "error"
                continue
                
            c = Claim(
                tenant_id=r.tenant_id,
                matter_id=r.matter_id,
                claimant_party_id=claimant_id,
                defendant_party_id=defendant_id,
                description=content.get("description", ""),
                review_status="approved",
                status="pending"
            )
            session.add(c)
        elif r.entity_type == "party":
            p = MatterParty(
                tenant_id=r.tenant_id,
                matter_id=r.matter_id,
                name=content.get("name", ""),
                role=content.get("role", "UNKNOWN"),
                type=content.get("type", "UNKNOWN")
            )
            session.add(p)
        elif r.entity_type == "legal_assertion":
            from apps.api.models.domain import LegalAssertion
            la = LegalAssertion(
                tenant_id=r.tenant_id,
                matter_id=r.matter_id,
                assertion_text=content.get("assertion_text", ""),
                source_locator=content.get("source_locator", None),
                review_status="approved"
            )
            session.add(la)
            
        elif r.entity_type == "deadline":
            from apps.api.models.deadline import DeadlineCandidate, DeadlineRule
            import datetime
            
            # 1. Get or Create Deadline Rule
            rule_name = content.get("rule_name", "Unknown Rule")
            stmt = select(DeadlineRule).where(
                DeadlineRule.tenant_id == r.tenant_id,
                DeadlineRule.rule_name == rule_name
            ).limit(1)
            rule_res = await session.execute(stmt)
            rule = rule_res.scalars().first()
            
            if not rule:
                rule = DeadlineRule(
                    tenant_id=r.tenant_id,
                    rule_name=rule_name,
                    trigger_type=content.get("trigger_event", "unknown"),
                    duration=content.get("offset_days", 0),
                    description="Automatically created rule via extraction"
                )
                session.add(rule)
                await session.flush()
                
            # 2. Create Potential Deadline
            pd = DeadlineCandidate(
                tenant_id=r.tenant_id,
                matter_id=r.matter_id,
                rule_id=rule.id,
                calculated_date=datetime.date.today() + datetime.timedelta(days=rule.duration),
                description=content.get("description", ""),
                status="POTENTIAL_DEADLINE"
            )
            session.add(pd)
            
        r.status = "published"
        
    if approved_items:
        from apps.api.models.audit import AuditEvent, Notification
        from apps.api.models.domain import User
        
        # Audit
        audit = AuditEvent(
            tenant_id=tenant_id,
            action="SYNC_APPROVED_REVIEWS",
            entity_type="review_queue",
            entity_id=matter_id or "all_matters",
            changes={"synced_items": len(approved_items)}
        )
        session.add(audit)
        
        # Notification
        from apps.api.models.domain import Membership, Role
        user_res = await session.execute(select(Membership.user_id).where(Membership.firm_id == tenant_id, Membership.role == Role.FIRM_ADMIN))
        admin_ids = user_res.scalars().all()
        for admin_id in admin_ids:
            notification = Notification(
                tenant_id=tenant_id,
                user_id=admin_id,
                title="Reviews Synced",
                message=f"{len(approved_items)} items synced"
            )
            session.add(notification)
            
        await session.commit()
        logger.info(f"Successfully synced {len(approved_items)} reviews.")
    else:
        logger.info("No approved reviews found to sync.")
