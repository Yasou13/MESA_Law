import hashlib
import json
import logging
from datetime import timedelta
from typing import Any, NoReturn

from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.core.observability import increment_metric, mutation_id_cv
from apps.api.core.ports.mesa_v4 import (
    DocumentRequest,
    MemoryInsertRequest,
    MesaV4Error,
    RevisionRequest,
    SessionStartRequest,
    SourceChunkRequest,
)
from apps.api.core.utils import utc_now
from apps.api.models.document import Document, DocumentRevision
from apps.api.models.domain import LegalAssertion, MatterParty, SourceLocator
from apps.api.models.mesa import MesaScopeBinding, MesaSyncRecord
from apps.api.models.parser import DocumentChunk, ParsedPage
from apps.api.models.queue import Job
from apps.api.models.review import ExtractionSuggestion, ReviewItem, ReviewState
from apps.worker.jobs import RetryableJobError, TerminalJobError
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.sync")


class PartyContent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    name: str = Field(min_length=1, max_length=300)
    role: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=100)


class ClaimContent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    description: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(default=0.0, ge=0, le=1)
    claimant_party_id: str | None = None
    defendant_party_id: str | None = None


class DeadlineContent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    trigger_event: str = Field(min_length=1, max_length=500)
    rule_name: str = Field(min_length=1, max_length=500)
    offset_days: int = Field(ge=0, le=36500)
    description: str = Field(min_length=1, max_length=5000)


class EvidenceContent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    description: str = Field(min_length=1, max_length=5000)
    relevance: str = Field(min_length=1, max_length=100)


CONTENT_ADAPTERS: dict[str, TypeAdapter[Any]] = {
    "party": TypeAdapter(PartyContent),
    "claim": TypeAdapter(ClaimContent),
    "deadline": TypeAdapter(DeadlineContent),
    "evidence": TypeAdapter(EvidenceContent),
}


def canonical_assertion_fields(
    entity_type: str, content: dict, matter_id: str
) -> dict[str, Any]:
    adapter = CONTENT_ADAPTERS.get(entity_type)
    if adapter is None:
        raise TerminalJobError(f"Unsupported reviewed entity type: {entity_type}")
    try:
        validated = adapter.validate_python(content)
    except ValidationError as exc:
        raise TerminalJobError(f"Reviewed content is invalid: {exc}") from exc
    data = validated.model_dump()
    if entity_type == "party":
        return {
            "assertion_type": "PARTY_ROLE",
            "subject_text": data["name"],
            "predicate": "HAS_MATTER_ROLE",
            "object_text": data["role"],
            "object_data": {"party_type": data["type"]},
            "assertion_text": f"{data['name']} has matter role {data['role']}",
            "polarity": "POSITIVE",
            "modality": "ASSERTED",
        }
    if entity_type == "claim":
        subject = data.get("claimant_party_id") or f"matter:{matter_id}"
        return {
            "assertion_type": "LEGAL_CLAIM",
            "subject_text": subject,
            "predicate": "ASSERTS_CLAIM",
            "object_text": data["description"],
            "object_data": {
                "defendant_party_id": data.get("defendant_party_id"),
                "confidence": data["confidence"],
            },
            "assertion_text": data["description"],
            "polarity": "POSITIVE",
            "modality": "ALLEGED",
        }
    if entity_type == "deadline":
        return {
            "assertion_type": "DEADLINE_TRIGGER",
            "subject_text": data["trigger_event"],
            "predicate": "MAY_TRIGGER_DEADLINE",
            "object_text": data["rule_name"],
            "object_data": {
                "offset_days": data["offset_days"],
                "description": data["description"],
            },
            "assertion_text": data["description"],
            "polarity": "POSITIVE",
            "modality": "POTENTIAL",
        }
    return {
        "assertion_type": "EVIDENCE_REFERENCE",
        "subject_text": f"matter:{matter_id}",
        "predicate": "HAS_EVIDENCE",
        "object_text": data["description"],
        "object_data": {"relevance": data["relevance"]},
        "assertion_text": data["description"],
        "polarity": "POSITIVE",
        "modality": "ASSERTED",
    }


def _raise_mesa_job_error(exc: MesaV4Error) -> NoReturn:
    message = f"MESA v4 error: {exc}"
    if exc.detail:
        message = f"{message} ({exc.detail})"
    if exc.retryable:
        raise RetryableJobError(message) from exc
    raise TerminalJobError(message) from exc


async def handle_provision_mesa_scope(payload: dict, session: AsyncSession) -> None:
    binding = await session.get(MesaScopeBinding, payload.get("binding_id"))
    if binding is None or binding.matter_id != payload.get("matter_id"):
        raise TerminalJobError("MESA scope binding not found")
    adapter = MesaV4HttpAdapter()
    try:
        await adapter.preflight_scope(
            tenant_id=binding.mesa_tenant_id,
            workspace_id=binding.workspace_id,
            dataset_id=binding.dataset_id,
        )
    except MesaV4Error as exc:
        _raise_mesa_job_error(exc)
    finally:
        await adapter.close()
    binding.provisioning_status = "READY"
    binding.last_verified_at = utc_now()
    binding.last_error = None


async def _publication_sources(
    session: AsyncSession, review: ReviewItem
) -> tuple[
    ExtractionSuggestion,
    SourceLocator,
    DocumentChunk,
    ParsedPage,
    DocumentRevision,
    Document,
]:
    suggestion = (
        await session.get(ExtractionSuggestion, review.suggestion_id)
        if review.suggestion_id
        else None
    )
    if suggestion is None or suggestion.matter_id != review.matter_id:
        raise TerminalJobError("Reviewed suggestion is missing or outside matter scope")
    locator = (
        await session.get(SourceLocator, suggestion.source_locator_id)
        if suggestion.source_locator_id
        else None
    )
    if (
        locator is None
        or locator.matter_id != review.matter_id
        or locator.chunk_id is None
        or locator.parsed_page_id is None
        or locator.document_revision_id is None
        or locator.evidence_text is None
        or locator.evidence_sha256 is None
    ):
        raise TerminalJobError("Review has no exact local source locator")
    chunk = await session.get(DocumentChunk, locator.chunk_id)
    page = await session.get(ParsedPage, locator.parsed_page_id)
    revision = await session.get(DocumentRevision, locator.document_revision_id)
    document = await session.get(Document, locator.document_id)
    if (
        chunk is None
        or page is None
        or revision is None
        or document is None
        or not revision.is_canonical
        or document.matter_id != review.matter_id
        or chunk.revision_id != revision.id
        or chunk.page_id != page.id
        or locator.character_start is None
        or locator.character_end is None
    ):
        raise TerminalJobError("Review provenance failed local relational verification")
    evidence = page.text_content[locator.character_start : locator.character_end]
    if (
        evidence != locator.evidence_text
        or hashlib.sha256(evidence.encode()).hexdigest() != locator.evidence_sha256
    ):
        raise TerminalJobError("Review evidence text/hash no longer resolves locally")
    return suggestion, locator, chunk, page, revision, document


async def handle_publish_review(payload: dict, session: AsyncSession) -> None:
    review_id = payload.get("review_id")
    review = await session.get(ReviewItem, review_id) if review_id else None
    if review is None or review.matter_id != payload.get("matter_id"):
        raise TerminalJobError("Review not found for publication")
    if review.status not in {ReviewState.APPROVED, ReviewState.CORRECTED}:
        raise TerminalJobError(f"Review {review.id} is not approved for publication")
    decision_version = review.version_id
    content = review.corrected_content or review.proposed_content
    assertion_fields = canonical_assertion_fields(
        review.entity_type, content, review.matter_id
    )
    suggestion, locator, chunk, page, revision, document = await _publication_sources(
        session, review
    )
    binding = await session.scalar(
        select(MesaScopeBinding).where(
            MesaScopeBinding.tenant_id == review.tenant_id,
            MesaScopeBinding.matter_id == review.matter_id,
        )
    )
    if binding is None or binding.provisioning_status != "READY":
        raise TerminalJobError("Matter MESA scope has not passed preflight")

    assertion = await session.scalar(
        select(LegalAssertion).where(LegalAssertion.review_id == review.id)
    )
    if assertion is None:
        assertion = LegalAssertion(
            tenant_id=review.tenant_id,
            matter_id=review.matter_id,
            source_locator_id=locator.id,
            review_id=review.id,
            review_version=decision_version,
            review_status="REVIEWED",
            canonical_status="REVIEWED",
            publication_status="PUBLISHING",
            **assertion_fields,
        )
        session.add(assertion)
        await session.flush()
        if review.entity_type == "party":
            party = PartyContent.model_validate(content)
            session.add(
                MatterParty(
                    tenant_id=review.tenant_id,
                    matter_id=review.matter_id,
                    name=party.name,
                    role=party.role,
                    type=party.type,
                    source_locator_id=locator.id,
                )
            )

    review.status = ReviewState.PUBLISHING
    review.version_id += 1
    suggestion.review_state = ReviewState.PUBLISHING.value
    assertion.publication_status = "PUBLISHING"
    idempotency_key = f"assertion:{assertion.id}:v{decision_version}"
    source_ref = (
        f"mesa-law://{review.tenant_id}/{review.matter_id}/{document.id}/"
        f"{revision.id}/{chunk.id}"
    )
    metadata = {
        "matter_id": review.matter_id,
        "source_locator_id": locator.id,
        "page_number": page.page_number,
        "character_start": locator.character_start,
        "character_end": locator.character_end,
        "evidence_text": locator.evidence_text,
        "evidence_sha256": locator.evidence_sha256,
        "provenance_state": locator.provenance_state,
        "assertion_id": assertion.id,
    }
    evidence_span = locator.evidence_text
    if evidence_span is None:
        raise TerminalJobError("Reviewed locator has no evidence text")
    stable_payload = {
        "dataset_id": binding.dataset_id,
        "document_id": document.id,
        "revision_id": revision.id,
        "chunk_id": chunk.id,
        "assertion": assertion_fields,
        "source_ref": source_ref,
        "metadata": metadata,
        "idempotency_key": idempotency_key,
    }
    serialized = json.dumps(
        stable_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    payload_hash = hashlib.sha256(serialized.encode()).hexdigest()
    sync_record = await session.scalar(
        select(MesaSyncRecord).where(
            MesaSyncRecord.tenant_id == review.tenant_id,
            MesaSyncRecord.idempotency_key == idempotency_key,
        )
    )
    if sync_record is None:
        sync_record = MesaSyncRecord(
            tenant_id=review.tenant_id,
            matter_id=review.matter_id,
            binding_id=binding.id,
            source_locator_id=locator.id,
            assertion_id=assertion.id,
            resource_type="LEGAL_ASSERTION",
            resource_id=assertion.id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            request_payload=stable_payload,
            status="PENDING_ADMISSION",
            is_terminal=False,
            attempts=0,
        )
        session.add(sync_record)
        await session.flush()
    elif sync_record.payload_hash != payload_hash:
        raise TerminalJobError("MESA idempotency key payload hash mismatch")

    adapter = MesaV4HttpAdapter()
    try:
        await adapter.preflight_scope(
            tenant_id=binding.mesa_tenant_id,
            workspace_id=binding.workspace_id,
            dataset_id=binding.dataset_id,
        )
        await adapter.create_document(
            DocumentRequest(
                tenant_id=binding.mesa_tenant_id,
                workspace_id=binding.workspace_id,
                dataset_id=binding.dataset_id,
                document_id=document.id,
                title=document.title,
                external_ref=f"mesa-law://{review.tenant_id}/{review.matter_id}/{document.id}",
            )
        )
        await adapter.create_revision(
            RevisionRequest(
                tenant_id=binding.mesa_tenant_id,
                workspace_id=binding.workspace_id,
                dataset_id=binding.dataset_id,
                document_id=document.id,
                revision_id=revision.id,
                revision_number=revision.version,
                content_sha256=revision.file_hash or "",
            )
        )
        await adapter.create_source_chunk(
            SourceChunkRequest(
                tenant_id=binding.mesa_tenant_id,
                workspace_id=binding.workspace_id,
                dataset_id=binding.dataset_id,
                document_id=document.id,
                revision_id=revision.id,
                chunk_id=chunk.id,
                title=document.title,
                content=chunk.text_content,
                source_ref=source_ref,
                revision_number=revision.version,
                chunk_ordinal=chunk.chunk_index,
            )
        )
        mesa_session = await adapter.start_session(
            SessionStartRequest(
                tenant_id=binding.mesa_tenant_id,
                workspace_id=binding.workspace_id,
                dataset_ids=[binding.dataset_id],
                agent_id=binding.agent_id,
            )
        )
        admission = await adapter.insert_memory(
            MemoryInsertRequest(
                session_id=mesa_session.session_id,
                dataset_id=binding.dataset_id,
                document_id=document.id,
                revision_id=revision.id,
                chunk_id=chunk.id,
                title=document.title,
                source_ref=source_ref,
                content=serialized,
                evidence_span=evidence_span,
                revision_number=revision.version,
                chunk_ordinal=chunk.chunk_index,
                metadata=metadata,
                idempotency_key=idempotency_key,
            )
        )
    except MesaV4Error as exc:
        _raise_mesa_job_error(exc)
    finally:
        await adapter.close()

    sync_record.session_id = mesa_session.session_id
    sync_record.mutation_id = admission.mutation_id
    sync_record.candidate_id = admission.candidate_id
    sync_record.pipeline_run_id = admission.pipeline_run_id
    sync_record.status = "ADMITTED"
    sync_record.attempts += 1
    session.add(
        Job(
            type="POLL_MESA_MUTATION",
            tenant_id=review.tenant_id,
            matter_id=review.matter_id,
            idempotency_key=f"poll:{sync_record.id}:0",
            run_at=utc_now() + timedelta(seconds=2),
            payload={
                "sync_record_id": sync_record.id,
                "matter_id": review.matter_id,
            },
        )
    )


async def handle_poll_mesa_mutation(payload: dict, session: AsyncSession) -> None:
    record = await session.get(MesaSyncRecord, payload.get("sync_record_id"))
    if record is None or record.matter_id != payload.get("matter_id"):
        raise TerminalJobError("MESA sync record not found")
    if record.is_terminal:
        return
    if not record.mutation_id:
        raise TerminalJobError("MESA sync record has no admitted mutation")
    assertion = (
        await session.get(LegalAssertion, record.assertion_id)
        if record.assertion_id
        else None
    )
    if assertion is None or assertion.review_id is None:
        raise TerminalJobError("MESA sync record lost its canonical assertion")
    review = await session.get(ReviewItem, assertion.review_id)
    if review is None:
        raise TerminalJobError("Published assertion lost its review audit record")

    mutation_token = mutation_id_cv.set(record.mutation_id)
    adapter = MesaV4HttpAdapter()
    try:
        mutation = await adapter.mutation_status(record.mutation_id)
    except MesaV4Error as exc:
        _raise_mesa_job_error(exc)
    finally:
        await adapter.close()
        mutation_id_cv.reset(mutation_token)

    record.attempts += 1
    record.last_polled_at = utc_now()
    record.status = mutation.state
    if mutation.is_terminal:
        increment_metric(
            "mesa_mutation_terminal_total",
            attributes={"state": mutation.state},
        )
        record.is_terminal = True
        if mutation.state == "COMMITTED":
            assertion.publication_status = "PUBLISHED"
            review.status = ReviewState.PUBLISHED
        else:
            reason = (
                mutation.rejection_reason or mutation.failure_class or mutation.state
            )
            record.last_error = reason
            assertion.publication_status = "PUBLICATION_FAILED"
            review.status = ReviewState.PUBLICATION_FAILED
        if review.suggestion_id:
            suggestion = await session.get(ExtractionSuggestion, review.suggestion_id)
            if suggestion is not None:
                suggestion.review_state = review.status.value
        review.version_id += 1
        return

    session.add(
        Job(
            type="POLL_MESA_MUTATION",
            tenant_id=record.tenant_id,
            matter_id=record.matter_id,
            idempotency_key=f"poll:{record.id}:{record.attempts}",
            run_at=utc_now() + timedelta(seconds=min(60, 2 ** min(record.attempts, 5))),
            payload={
                "sync_record_id": record.id,
                "matter_id": record.matter_id,
            },
        )
    )


async def handle_build_lexical_index(payload: dict, session: AsyncSession) -> None:
    logger.info("Building lexical index for matter %s", payload.get("matter_id"))
    try:
        await session.execute(text("ANALYZE parsed_pages"))
    except Exception as exc:
        raise RetryableJobError(f"Lexical index maintenance failed: {exc}") from exc
