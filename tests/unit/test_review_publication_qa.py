import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apps.api.core.ports.intelligence import Evidence
from apps.api.core.ports.mesa_v4 import (
    AdmissionResponse,
    MutationStatusResponse,
    SessionResponse,
)
from apps.api.core.qa import (
    _citation_from_local_chunk,
    _verify_mesa_evidence,
    ask_matter_question,
)
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.domain import LegalAssertion, SourceLocator
from apps.api.models.mesa import MesaScopeBinding, MesaSyncRecord
from apps.api.models.parser import DocumentChunk, ParsedPage
from apps.api.models.queue import Job
from apps.api.models.review import ExtractionSuggestion, ReviewItem, ReviewState
from apps.api.routers.reviews import CorrectReviewRequest, _transition_proposal
from apps.worker.handlers.sync import (
    canonical_assertion_fields,
    handle_poll_mesa_mutation,
    handle_publish_review,
)
from apps.worker.jobs import TerminalJobError
from fastapi import HTTPException
from pydantic import ValidationError


def make_review(status: ReviewState = ReviewState.PROPOSED) -> ReviewItem:
    return ReviewItem(
        id="review-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        entity_type="party",
        entity_id="proposal-1",
        suggestion_id="suggestion-1",
        proposed_content={"name": "Ayşe", "role": "DAVACI", "type": "PERSON"},
        status=status,
        version_id=2,
    )


@pytest.mark.asyncio
async def test_stale_review_version_is_rejected_before_mutation() -> None:
    session = AsyncMock()
    with pytest.raises(HTTPException) as raised:
        await _transition_proposal(
            session,
            review=make_review(),
            expected_version=1,
            target=ReviewState.APPROVED,
            principal_id="user-1",
            reason=None,
        )
    assert raised.value.status_code == 409
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_atomic_review_race_returns_conflict() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    with pytest.raises(HTTPException) as raised:
        await _transition_proposal(
            session,
            review=make_review(),
            expected_version=2,
            target=ReviewState.CORRECTED,
            principal_id="user-1",
            reason="Yanlış rol",
            corrected_content={"name": "Ayşe", "role": "DAVALI", "type": "PERSON"},
        )
    assert raised.value.status_code == 409


def test_correction_requires_version_reason_and_content() -> None:
    with pytest.raises(ValidationError):
        CorrectReviewRequest.model_validate(
            {"expected_version": 2, "reason": "x", "corrected_content": {}}
        )


def test_canonical_assertion_is_typed_and_strict() -> None:
    fields = canonical_assertion_fields(
        "party", {"name": "Ayşe", "role": "DAVACI", "type": "PERSON"}, "matter-1"
    )
    assert fields["assertion_type"] == "PARTY_ROLE"
    assert fields["subject_text"] == "Ayşe"
    with pytest.raises(TerminalJobError):
        canonical_assertion_fields(
            "party", {"name": "Ayşe", "role": "DAVACI", "extra": True}, "matter-1"
        )


def publication_objects():
    review = make_review(ReviewState.APPROVED)
    evidence = "Davacı Ayşe"
    digest = hashlib.sha256(evidence.encode()).hexdigest()
    suggestion = ExtractionSuggestion(
        id="suggestion-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        document_id="document-1",
        document_revision_id="revision-1",
        source_locator_id="locator-1",
        suggestion_type="PARTY_SUGGESTION",
        payload=review.proposed_content,
        extractor_name="heuristic",
        extractor_version="v1",
        prompt_version="none",
        parser_version="parser-v2",
        idempotency_key="suggestion-key",
    )
    locator = SourceLocator(
        id="locator-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        document_id="document-1",
        document_revision_id="revision-1",
        parsed_document_id="parsed-1",
        parsed_page_id="page-1",
        chunk_id="chunk-1",
        page_number=1,
        character_start=0,
        character_end=len(evidence),
        evidence_text=evidence,
        evidence_sha256=digest,
        provenance_state="VERIFIED_PDF",
    )
    page = ParsedPage(
        id="page-1",
        parsed_document_id="parsed-1",
        page_number=1,
        text_content=evidence,
    )
    chunk = DocumentChunk(
        id="chunk-1",
        tenant_id="tenant-1",
        document_id="document-1",
        revision_id="revision-1",
        page_id="page-1",
        chunk_index=0,
        chunk_type="block",
        text_content=evidence,
        watermarked_text=evidence,
        character_start=0,
        character_end=len(evidence),
        content_sha256=digest,
        provenance_state="VERIFIED_PDF",
    )
    revision = DocumentRevision(
        id="revision-1",
        tenant_id="tenant-1",
        document_id="document-1",
        version=1,
        s3_key="immutable/revision.pdf",
        is_canonical=True,
        file_hash="a" * 64,
        size_bytes=10,
        mime_type="application/pdf",
        scan_status=DocumentState.READY,
    )
    document = Document(
        id="document-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        title="Dilekçe.pdf",
    )
    binding = MesaScopeBinding(
        id="binding-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        mesa_tenant_id="mesa-tenant",
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        agent_id="agent-1",
        provisioning_status="READY",
    )
    assertion = LegalAssertion(
        id="assertion-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        review_id=review.id,
        review_version=review.version_id,
        assertion_text="Ayşe has matter role DAVACI",
        source_locator_id=locator.id,
        review_status="REVIEWED",
        assertion_type="PARTY_ROLE",
        subject_text="Ayşe",
        predicate="HAS_MATTER_ROLE",
        object_text="DAVACI",
        canonical_status="REVIEWED",
        publication_status="NOT_PUBLISHED",
    )
    return (
        review,
        suggestion,
        locator,
        chunk,
        page,
        revision,
        document,
        binding,
        assertion,
    )


@pytest.mark.asyncio
async def test_admission_only_moves_review_to_publishing() -> None:
    review, suggestion, locator, chunk, page, revision, document, binding, assertion = (
        publication_objects()
    )
    session = AsyncMock()
    added: list[object] = []

    def add(value: object) -> None:
        if isinstance(value, MesaSyncRecord) and value.id is None:
            value.id = "sync-1"
        added.append(value)

    async def get(model: type, object_id: str):
        return {
            ReviewItem: review,
            ExtractionSuggestion: suggestion,
            SourceLocator: locator,
            DocumentChunk: chunk,
            ParsedPage: page,
            DocumentRevision: revision,
            Document: document,
        }.get(model)

    session.add = MagicMock(side_effect=add)
    session.get.side_effect = get
    session.scalar.side_effect = [binding, assertion, None]
    adapter = AsyncMock()
    adapter.start_session.return_value = SessionResponse(
        session_id="mesa-session-1",
        tenant_id="mesa-tenant",
        workspace_id="workspace-1",
        dataset_ids=["dataset-1"],
        agent_id="agent-1",
        status="ACTIVE",
    )
    adapter.insert_memory.return_value = AdmissionResponse(
        status="accepted",
        mutation_id="mutation-1",
        candidate_id="candidate-1",
        pipeline_run_id="pipeline-1",
        raw_log_id=1,
    )

    with patch("apps.worker.handlers.sync.MesaV4HttpAdapter", return_value=adapter):
        await handle_publish_review(
            {"review_id": review.id, "matter_id": review.matter_id}, session
        )

    record = next(item for item in added if isinstance(item, MesaSyncRecord))
    assert review.status == ReviewState.PUBLISHING
    assert assertion.publication_status == "PUBLISHING"
    assert record.status == "ADMITTED"
    assert record.mutation_id == "mutation-1"
    assert any(
        isinstance(item, Job) and item.type == "POLL_MESA_MUTATION" for item in added
    )
    assert review.status != ReviewState.PUBLISHED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mutation_state", "review_state"),
    [
        ("COMMITTED", ReviewState.PUBLISHED),
        ("REJECTED", ReviewState.PUBLICATION_FAILED),
        ("DEAD_LETTER", ReviewState.PUBLICATION_FAILED),
        ("ROLLED_BACK", ReviewState.PUBLICATION_FAILED),
        ("BLOCKED", ReviewState.PUBLICATION_FAILED),
    ],
)
async def test_only_terminal_mutation_sets_final_publication_state(
    mutation_state: str, review_state: ReviewState
) -> None:
    review = make_review(ReviewState.PUBLISHING)
    assertion = LegalAssertion(
        id="assertion-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        review_id=review.id,
        assertion_text="assertion",
        publication_status="PUBLISHING",
    )
    record = MesaSyncRecord(
        id="sync-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        binding_id="binding-1",
        assertion_id=assertion.id,
        resource_type="LEGAL_ASSERTION",
        resource_id=assertion.id,
        idempotency_key="idem",
        payload_hash="a" * 64,
        request_payload={},
        mutation_id="mutation-1",
        status="ADMITTED",
        is_terminal=False,
        attempts=1,
    )
    suggestion = ExtractionSuggestion(
        id=review.suggestion_id,
        tenant_id="tenant-1",
        matter_id="matter-1",
        document_id="document-1",
        document_revision_id="revision-1",
        suggestion_type="CLAIM_SUGGESTION",
        payload={},
        extractor_name="heuristic",
        extractor_version="v1",
        prompt_version="none",
        parser_version="parser-v2",
        review_state=ReviewState.PUBLISHING.value,
        idempotency_key=f"suggestion-{mutation_state.lower()}",
    )
    session = AsyncMock()
    session.get.side_effect = [record, assertion, review, suggestion]
    adapter = AsyncMock()
    adapter.mutation_status.return_value = MutationStatusResponse(
        mutation_id="mutation-1",
        candidate_id="candidate-1",
        state=mutation_state,
        rejection_reason="rejected" if mutation_state != "COMMITTED" else None,
    )
    with patch("apps.worker.handlers.sync.MesaV4HttpAdapter", return_value=adapter):
        await handle_poll_mesa_mutation(
            {"sync_record_id": record.id, "matter_id": record.matter_id}, session
        )
    assert record.is_terminal is True
    assert record.status == mutation_state
    assert review.status == review_state
    assert assertion.publication_status == (
        "PUBLISHED" if mutation_state == "COMMITTED" else "PUBLICATION_FAILED"
    )
    assert suggestion.review_state == review_state.value


@pytest.mark.asyncio
async def test_nonterminal_mutation_schedules_another_poll_without_publishing() -> None:
    review = make_review(ReviewState.PUBLISHING)
    assertion = LegalAssertion(
        id="assertion-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        review_id=review.id,
        assertion_text="assertion",
        publication_status="PUBLISHING",
    )
    record = MesaSyncRecord(
        id="sync-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        binding_id="binding-1",
        assertion_id=assertion.id,
        resource_type="LEGAL_ASSERTION",
        resource_id=assertion.id,
        idempotency_key="idem",
        payload_hash="a" * 64,
        request_payload={},
        mutation_id="mutation-1",
        status="ADMITTED",
        is_terminal=False,
        attempts=1,
    )
    session = AsyncMock()
    session.add = MagicMock()
    session.get.side_effect = [record, assertion, review]
    adapter = AsyncMock()
    adapter.mutation_status.return_value = MutationStatusResponse(
        mutation_id="mutation-1", candidate_id="candidate-1", state="RUNNING"
    )
    with patch("apps.worker.handlers.sync.MesaV4HttpAdapter", return_value=adapter):
        await handle_poll_mesa_mutation(
            {"sync_record_id": record.id, "matter_id": record.matter_id}, session
        )
    assert record.is_terminal is False
    assert review.status == ReviewState.PUBLISHING
    assert assertion.publication_status == "PUBLISHING"
    queued = session.add.call_args.args[0]
    assert isinstance(queued, Job) and queued.type == "POLL_MESA_MUTATION"


@pytest.mark.asyncio
async def test_mesa_provenance_must_match_local_locator_hash_and_scope() -> None:
    _, _, locator, chunk, page, revision, document, _, _ = publication_objects()
    session = AsyncMock()
    result = MagicMock()
    result.one_or_none.return_value = (locator, chunk, page, revision, document)
    session.execute.return_value = result
    source_ref = f"mesa-law://tenant-1/matter-1/{document.id}/{revision.id}/{chunk.id}"
    evidence = Evidence(
        dataset_id="dataset-1",
        document_id=document.id,
        revision_id=revision.id,
        chunk_id=chunk.id,
        source_ref=source_ref,
        evidence_span=locator.evidence_text or "",
        page_number=1,
        text_snippet=locator.evidence_text or "",
        metadata={
            "source_locator_id": locator.id,
            "evidence_sha256": locator.evidence_sha256,
        },
    )
    citation = await _verify_mesa_evidence(
        session,
        tenant_id="tenant-1",
        matter_id="matter-1",
        dataset_id="dataset-1",
        document_filter=None,
        evidence=evidence,
    )
    assert citation is not None
    evidence.metadata["evidence_sha256"] = "0" * 64
    assert (
        await _verify_mesa_evidence(
            session,
            tenant_id="tenant-1",
            matter_id="matter-1",
            dataset_id="dataset-1",
            document_filter=None,
            evidence=evidence,
        )
        is None
    )


def test_qa_citation_rejects_tampered_text_and_marks_low_provenance() -> None:
    text = "Sözleşme 1 Ocak tarihinde imzalandı."
    digest = hashlib.sha256(text.encode()).hexdigest()
    page = ParsedPage(
        id="page-1", parsed_document_id="parsed-1", page_number=0, text_content=text
    )
    chunk = DocumentChunk(
        id="chunk-1",
        tenant_id="tenant-1",
        document_id="document-1",
        revision_id="revision-1",
        page_id=page.id,
        chunk_index=0,
        chunk_type="text_span",
        text_content=text,
        watermarked_text=text,
        character_start=0,
        character_end=len(text),
        content_sha256=digest,
        provenance_state="LOW_PROVENANCE",
    )
    revision = DocumentRevision(
        id="revision-1",
        tenant_id="tenant-1",
        document_id="document-1",
        version=1,
        s3_key="immutable/file.txt",
        is_canonical=True,
        immutable_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        file_hash="a" * 64,
        mime_type="text/plain",
        scan_status=DocumentState.READY,
    )
    citation = _citation_from_local_chunk(chunk, page, revision)
    assert citation is not None
    assert citation.page_number is None
    assert citation.low_provenance is True
    chunk.text_content = "tampered"
    assert _citation_from_local_chunk(chunk, page, revision) is None


@pytest.mark.asyncio
async def test_qa_abstains_without_verified_evidence_even_in_test_env() -> None:
    session = AsyncMock()
    session.scalar.return_value = None
    result = MagicMock()
    result.all.return_value = []
    session.execute.return_value = result
    response = await ask_matter_question(
        session, "tenant-1", "matter-1", None, "Sözleşme ne zaman imzalandı?"
    )
    assert response.status == "ABSTAIN"
    assert response.citations == []
    assert "yeterli doğrulanmış" in response.answer
