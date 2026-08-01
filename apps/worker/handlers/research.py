import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.research")


async def handle_perform_legal_research(payload: dict, session: AsyncSession):
    matter_id = payload.get("matter_id")
    query = payload.get("query")
    tenant_id = payload.get("tenant_id")

    if not all([matter_id, query, tenant_id]):
        logger.error("Missing fields in PERFORM_LEGAL_RESEARCH")
        return

    logger.info(f"Performing legal research for query: '{query}' on matter {matter_id}")

    # 1. Mock External API / Database Lookup
    from apps.api.models.research import LegalSource

    stmt = (
        select(LegalSource)
        .where(
            or_(
                LegalSource.title.ilike(f"%{query}%"),
                LegalSource.content.ilike(f"%{query}%"),
                LegalSource.citation.ilike(f"%{query}%"),
            )
        )
        .limit(3)
    )

    result = await session.execute(stmt)
    resources = result.scalars().all()

    if not resources:
        logger.info("No research results found.")
        return

    # 2. Add to ReviewQueue as LegalAssertion Drafts
    import hashlib
    import json

    import uuid6
    from apps.api.models.review import ExtractionSuggestion, ReviewItem

    def generate_idempotency_key(type_str: str, locator: str) -> str:
        raw = f"{matter_id}_research_{query}_{type_str}_{locator}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    for r in resources:
        ik = generate_idempotency_key("LEGAL_ISSUE_SUGGESTION", str(r.id))

        # Check idempotency
        existing_sugg = await session.execute(
            select(ExtractionSuggestion).where(
                ExtractionSuggestion.idempotency_key == ik
            )
        )
        if existing_sugg.scalars().first():
            logger.info(f"Skipping duplicate LEGAL_ISSUE_SUGGESTION {ik}")
            continue

        suggestion = ExtractionSuggestion(
            tenant_id=tenant_id,
            matter_id=matter_id,
            document_id="research_task",
            document_revision_id="research_task",
            source_locator_id=str(r.id),
            suggestion_type="LEGAL_ISSUE_SUGGESTION",
            payload={
                "assertion_text": f"Found relevant legal precedent: {r.title} - {r.content[:150]}...",
                "source_locator": json.dumps(
                    {
                        "type": "Legislation"
                        if "Kanun" in r.title or "Madde" in r.title
                        else "Case Law",
                        "title": r.title,
                        "citation": r.citation,
                        "id": str(r.id),
                    }
                ),
            },
            extractor_name="MesaIntelligencePort",
            extractor_version="1.0.0",
            prompt_version="1.0",
            parser_version="research",
            idempotency_key=ik,
        )
        session.add(suggestion)
        await session.flush()

        review_item = ReviewItem(
            tenant_id=tenant_id,
            matter_id=matter_id,
            entity_type="legal_assertion",
            entity_id=f"draft_assertion_{uuid6.uuid7()}",
            suggestion_id=suggestion.id,
            proposed_content=suggestion.payload,
            status="draft",
        )
        session.add(review_item)

    await session.commit()
    logger.info(f"Enqueued {len(resources)} research assertions to ReviewItem.")
