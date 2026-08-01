"""Additive source-aware read models remain scoped and secret-free."""

import inspect
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apps.api.core.models import RequestContext
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.domain import SourceLocator
from apps.api.models.parser import ParsedDocument
from apps.api.models.review import ExtractionSuggestion, ReviewItem, ReviewState
from apps.api.routers.documents import get_document_viewer_context
from apps.api.routers.reviews import get_review_context
from fastapi import HTTPException


def context(tenant_id: str = "tenant-1") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        principal_id="user-1",
        roles={"ATTORNEY"},
    )


def document(tenant_id: str = "tenant-1") -> Document:
    now = datetime.now(UTC)
    item = Document(
        tenant_id=tenant_id,
        matter_id="matter-1",
        title="Sözleşme.pdf",
    )
    item.id = "document-1"
    item.created_at = now
    item.updated_at = now
    return item


def canonical_revision() -> DocumentRevision:
    now = datetime.now(UTC)
    revision = DocumentRevision(
        tenant_id="tenant-1",
        document_id="document-1",
        version=4,
        s3_key="immutable/private-object.pdf",
        quarantine_key="quarantine/private-object.pdf",
        is_canonical=True,
        immutable_at=now,
        file_hash="a" * 64,
        size_bytes=2048,
        mime_type="application/pdf",
        scan_status=DocumentState.READY,
    )
    revision.id = "revision-4"
    return revision


@pytest.mark.asyncio
async def test_viewer_context_returns_canonical_metadata_without_storage_keys() -> None:
    db = AsyncMock()
    db.get.return_value = document()
    revision = canonical_revision()
    parsed = ParsedDocument(
        id="parsed-1",
        tenant_id="tenant-1",
        document_id="document-1",
        revision_id=revision.id,
        parsing_revision=2,
        parser_used="pymupdf",
        ocr_version=None,
        pipeline_version="pipeline-v2",
        status="completed",
        provenance_state="VERIFIED_PDF_TEXT",
    )
    db.scalar.side_effect = [revision, parsed]

    with patch(
        "apps.api.routers.documents.DocumentAccessPolicy.can_read",
        new_callable=AsyncMock,
    ):
        response = await inspect.unwrap(get_document_viewer_context)(
            request=MagicMock(),
            document_id="document-1",
            context=context(),
            db=db,
        )

    payload = response.model_dump(mode="json")
    assert payload["revision"]["id"] == revision.id
    assert payload["revision"]["sha256"] == "a" * 64
    assert payload["parsed_document"]["parser"] == "pymupdf"
    encoded = json.dumps(payload)
    assert "s3_key" not in encoded
    assert "quarantine_key" not in encoded
    assert "private-object" not in encoded


@pytest.mark.asyncio
async def test_viewer_context_hides_cross_tenant_document_existence() -> None:
    db = AsyncMock()
    db.get.return_value = document("tenant-2")

    with pytest.raises(HTTPException) as raised:
        await inspect.unwrap(get_document_viewer_context)(
            request=MagicMock(),
            document_id="document-1",
            context=context(),
            db=db,
        )

    assert raised.value.status_code == 404
    db.scalar.assert_not_awaited()


def review_with_suggestion() -> ReviewItem:
    review = ReviewItem(
        tenant_id="tenant-1",
        matter_id="matter-1",
        entity_type="legal_assertion",
        entity_id="assertion-1",
        suggestion_id="suggestion-1",
        proposed_content={"predicate": "owes", "object": "1000 TRY"},
        status=ReviewState.PROPOSED,
        version_id=1,
    )
    review.id = "review-1"
    return review


def suggestion(source_locator_id: str | None) -> ExtractionSuggestion:
    item = ExtractionSuggestion(
        tenant_id="tenant-1",
        matter_id="matter-1",
        document_id="document-1",
        document_revision_id="revision-4",
        source_locator_id=source_locator_id,
        suggestion_type="CONTRACT_OBLIGATION",
        payload={"predicate": "owes", "object": "1000 TRY"},
        extractor_name="rules",
        extractor_version="2.1",
        prompt_version="none",
        parser_version="pymupdf-1",
        confidence_category="medium",
        idempotency_key="suggestion-key",
    )
    item.id = "suggestion-1"
    return item


@pytest.mark.asyncio
async def test_review_context_exposes_exact_source_and_audit_history() -> None:
    review = review_with_suggestion()
    extracted = suggestion("locator-1")
    locator = SourceLocator(
        id="locator-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        document_id="document-1",
        document_revision_id="revision-4",
        parsed_document_id="parsed-1",
        parsed_page_id="page-7",
        chunk_id="chunk-7",
        page_number=7,
        character_start=12,
        character_end=36,
        bbox_x0=10.0,
        bbox_y0=20.0,
        bbox_x1=120.0,
        bbox_y1=42.0,
        evidence_text="Borç 1000 TRY tutarındadır.",
        evidence_sha256="b" * 64,
        parser_version="pymupdf-1",
        extraction_version="rules-2.1",
        provenance_state="VERIFIED_PDF_TEXT",
    )
    db = AsyncMock()
    db.scalar.side_effect = [review, extracted]
    source_result = MagicMock()
    source_result.one_or_none.return_value = (locator, document())
    history_result = MagicMock()
    history_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [source_result, history_result]

    with patch(
        "apps.api.routers.reviews.MatterAccessPolicy.can_read",
        new_callable=AsyncMock,
    ):
        response = await get_review_context(
            review_id="review-1", context=context(), db=db
        )

    assert response.suggestion is not None
    assert response.suggestion.confidence_category == "medium"
    assert response.source is not None
    assert response.source.revision_id == "revision-4"
    assert response.source.page_number == 7
    assert response.source.text_start == 12
    assert response.source.bbox == {"x0": 10.0, "y0": 20.0, "x1": 120.0, "y1": 42.0}


@pytest.mark.asyncio
async def test_legacy_review_without_locator_returns_null_source() -> None:
    db = AsyncMock()
    db.scalar.side_effect = [review_with_suggestion(), suggestion(None)]
    history_result = MagicMock()
    history_result.scalars.return_value.all.return_value = []
    db.execute.return_value = history_result

    with patch(
        "apps.api.routers.reviews.MatterAccessPolicy.can_read",
        new_callable=AsyncMock,
    ):
        response = await get_review_context(
            review_id="review-1", context=context(), db=db
        )

    assert response.source is None


@pytest.mark.asyncio
async def test_review_context_hides_cross_tenant_review_existence() -> None:
    db = AsyncMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as raised:
        await get_review_context(review_id="review-other", context=context(), db=db)

    assert raised.value.status_code == 404
