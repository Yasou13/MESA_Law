import hashlib
import logging
from dataclasses import dataclass

import uuid6
from apps.api.core.extraction import get_extraction_adapter
from apps.api.core.utils import utc_now
from apps.api.models.audit import AuditEvent, Notification
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.domain import MatterMember, SourceLocator
from apps.api.models.parser import DocumentChunk, ParsedDocument, ParsedPage
from apps.api.models.review import ExtractionSuggestion, ReviewItem, ReviewState
from apps.worker.jobs import TerminalJobError
from apps.worker.provenance import CHUNKING_VERSION
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.extraction")


@dataclass(frozen=True)
class ResolvedEvidence:
    chunk: DocumentChunk
    page: ParsedPage
    evidence_text: str
    character_start: int
    character_end: int


def resolve_evidence(
    evidence_text: str | None,
    chunks: list[tuple[DocumentChunk, ParsedPage]],
) -> ResolvedEvidence | None:
    if not evidence_text or not evidence_text.strip():
        return None
    needle = evidence_text.strip()
    for chunk, page in chunks:
        local_start = chunk.text_content.find(needle)
        if local_start < 0:
            local_start = chunk.text_content.casefold().find(needle.casefold())
        if local_start < 0 or chunk.character_start is None:
            continue
        actual = chunk.text_content[local_start : local_start + len(needle)]
        start = chunk.character_start + local_start
        return ResolvedEvidence(
            chunk=chunk,
            page=page,
            evidence_text=actual,
            character_start=start,
            character_end=start + len(actual),
        )
    return None


def make_locator(
    *,
    parsed_document: ParsedDocument,
    matter_id: str,
    resolved: ResolvedEvidence,
) -> SourceLocator:
    bbox = resolved.chunk.bbox or {}
    verified = resolved.chunk.provenance_state.startswith("VERIFIED_PDF")
    digest = hashlib.sha256(resolved.evidence_text.encode("utf-8")).hexdigest()
    return SourceLocator(
        tenant_id=parsed_document.tenant_id,
        matter_id=matter_id,
        document_id=parsed_document.document_id,
        document_revision_id=parsed_document.revision_id,
        parsed_document_id=parsed_document.id,
        parsed_page_id=resolved.page.id,
        chunk_id=resolved.chunk.id,
        page_number=resolved.page.page_number,
        character_start=resolved.character_start,
        character_end=resolved.character_end,
        bbox_x0=bbox.get("x0"),
        bbox_y0=bbox.get("y0"),
        bbox_x1=bbox.get("x1"),
        bbox_y1=bbox.get("y1"),
        text_snippet=resolved.evidence_text,
        text_hash=digest,
        evidence_text=resolved.evidence_text,
        evidence_sha256=digest,
        parser_version=parsed_document.parser_used,
        ocr_version=parsed_document.ocr_version,
        extraction_version=CHUNKING_VERSION,
        provenance_state=resolved.chunk.provenance_state,
        verified_at=utc_now() if verified else None,
    )


def suggestion_key(
    revision_id: str, suggestion_type: str, resolved: ResolvedEvidence
) -> str:
    raw = (
        f"{revision_id}:{suggestion_type}:{resolved.chunk.id}:"
        f"{resolved.character_start}:{resolved.character_end}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def handle_extract_legal_data(payload: dict, session: AsyncSession) -> None:
    parsed_document_id = payload.get("parsed_document_id")
    if not parsed_document_id:
        raise TerminalJobError("Missing parsed_document_id in payload")

    parsed_document = await session.get(ParsedDocument, parsed_document_id)
    if parsed_document is None:
        raise TerminalJobError(f"ParsedDocument {parsed_document_id} not found")
    document = await session.get(Document, parsed_document.document_id)
    revision = await session.get(DocumentRevision, parsed_document.revision_id)
    if document is None or revision is None or revision.document_id != document.id:
        raise TerminalJobError("Parsed document source revision is missing")
    if not revision.is_canonical:
        raise TerminalJobError("Extraction requires a canonical revision")

    rows = (
        await session.execute(
            select(DocumentChunk, ParsedPage)
            .join(ParsedPage, DocumentChunk.page_id == ParsedPage.id)
            .where(
                ParsedPage.parsed_document_id == parsed_document.id,
                DocumentChunk.revision_id == revision.id,
            )
            .order_by(ParsedPage.page_number, DocumentChunk.chunk_index)
        )
    ).all()
    chunks = [(chunk, page) for chunk, page in rows]
    if not chunks:
        raise TerminalJobError("Parsed document has no exact source chunks")
    full_text = "\n\n".join(chunk.text_content for chunk, _ in chunks)
    matter_id = document.matter_id
    adapter = get_extraction_adapter()

    party_data = await adapter.extract_parties(full_text)
    claim_data = await adapter.extract_claims(full_text)
    event_data = await adapter.extract_events(full_text)
    evidence_data = await adapter.extract_evidence(full_text)
    created_counts = {"parties": 0, "claims": 0, "events": 0, "evidence": 0}

    async def create_review(
        *,
        item: dict,
        suggestion_type: str,
        entity_type: str,
        proposed_content: dict,
    ) -> bool:
        resolved = resolve_evidence(item.get("evidence_text"), chunks)
        if resolved is None:
            logger.warning(
                "Discarded %s because its evidence did not resolve to a chunk",
                suggestion_type,
            )
            return False
        idempotency_key = suggestion_key(revision.id, suggestion_type, resolved)
        existing = await session.scalar(
            select(ExtractionSuggestion.id).where(
                ExtractionSuggestion.idempotency_key == idempotency_key
            )
        )
        if existing is not None:
            return False

        locator = make_locator(
            parsed_document=parsed_document,
            matter_id=matter_id,
            resolved=resolved,
        )
        session.add(locator)
        await session.flush()
        suggestion = ExtractionSuggestion(
            tenant_id=parsed_document.tenant_id,
            matter_id=matter_id,
            document_id=document.id,
            document_revision_id=revision.id,
            source_locator_id=locator.id,
            suggestion_type=suggestion_type,
            payload=proposed_content,
            extractor_name=type(adapter).__name__,
            extractor_version=str(item.get("version", "unknown")),
            prompt_version="not-applicable",
            parser_version=parsed_document.parser_used,
            confidence_category=(
                "high" if float(item.get("confidence", 0.0)) >= 0.8 else "medium"
            ),
            idempotency_key=idempotency_key,
        )
        session.add(suggestion)
        await session.flush()
        session.add(
            ReviewItem(
                tenant_id=parsed_document.tenant_id,
                matter_id=matter_id,
                entity_type=entity_type,
                entity_id=f"proposal-{uuid6.uuid7()}",
                suggestion_id=suggestion.id,
                proposed_content=proposed_content,
                status=ReviewState.PROPOSED,
            )
        )
        return True

    for item in party_data:
        if await create_review(
            item=item,
            suggestion_type="PARTY_SUGGESTION",
            entity_type="party",
            proposed_content={
                "name": item["name"],
                "role": item["role"],
                "type": item["type"],
            },
        ):
            created_counts["parties"] += 1
    for item in claim_data:
        if await create_review(
            item=item,
            suggestion_type="CLAIM_SUGGESTION",
            entity_type="claim",
            proposed_content={
                "description": item["description"],
                "confidence": item.get("confidence", 0.0),
            },
        ):
            created_counts["claims"] += 1
    for item in event_data:
        if await create_review(
            item=item,
            suggestion_type="DEADLINE_TRIGGER_SUGGESTION",
            entity_type="deadline",
            proposed_content={
                "trigger_event": item["trigger_event"],
                "rule_name": item["rule_name"],
                "offset_days": item["offset_days"],
                "description": item["description"],
            },
        ):
            created_counts["events"] += 1
    for item in evidence_data:
        if await create_review(
            item=item,
            suggestion_type="EVIDENCE_SUGGESTION",
            entity_type="evidence",
            proposed_content={
                "description": item["description"],
                "relevance": item["relevance"],
            },
        ):
            created_counts["evidence"] += 1

    revision.scan_status = DocumentState.READY
    session.add(
        AuditEvent(
            tenant_id=parsed_document.tenant_id,
            action="EXTRACTION_COMPLETED",
            entity_type="parsed_document",
            entity_id=parsed_document.id,
            changes=created_counts,
        )
    )
    member_ids = (
        await session.execute(
            select(MatterMember.user_id).where(
                MatterMember.tenant_id == parsed_document.tenant_id,
                MatterMember.matter_id == matter_id,
            )
        )
    ).scalars()
    for member_id in set(member_ids.all()):
        session.add(
            Notification(
                tenant_id=parsed_document.tenant_id,
                user_id=member_id,
                title="Extraction complete",
                message=f"Review queue updated for document {document.title}",
            )
        )
    logger.info("Exact-source extraction completed for %s", parsed_document.id)
