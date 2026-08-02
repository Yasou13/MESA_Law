import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import fitz
import pytest
from apps.api.core.storage import (
    ImmutableObjectConflictError,
    StorageIntegrityError,
    StorageService,
)
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.parser import DocumentChunk, ParsedPage
from apps.api.models.queue import Job
from apps.worker.handlers.document import handle_scan_document
from apps.worker.handlers.extraction import resolve_evidence
from apps.worker.jobs import TerminalJobError
from apps.worker.parsers.pdf import parse_pdf_bytes
from apps.worker.provenance import (
    LOW_PROVENANCE,
    VERIFIED_PDF,
    build_chunks,
    normalize_text,
    page_from_layout_blocks,
)


def test_layout_offsets_resolve_to_exact_normalized_text() -> None:
    page_text, blocks = page_from_layout_blocks(
        [
            {"id": "b0", "text": "  Davacı   Ayşe  ", "bbox": [1, 2, 30, 12]},
            {"id": "b1", "text": "Tazminat talep eder.", "bbox": [1, 20, 80, 32]},
        ]
    )
    assert page_text == "Davacı Ayşe\n\nTazminat talep eder."
    for block in blocks:
        assert (
            page_text[block["character_start"] : block["character_end"]]
            == block["text"]
        )

    chunks = build_chunks(
        page_text=page_text,
        page_number=1,
        content_identity="f" * 64,
        provenance_state=VERIFIED_PDF,
        layout_blocks=blocks,
    )
    assert [chunk.text for chunk in chunks] == [
        "Davacı Ayşe",
        "Tazminat talep eder.",
    ]
    for chunk in chunks:
        assert page_text[chunk.character_start : chunk.character_end] == chunk.text
        assert hashlib.sha256(chunk.text.encode()).hexdigest() == chunk.content_sha256
        assert chunk.bbox is not None


def test_chunk_ids_and_boundaries_are_deterministic() -> None:
    text = normalize_text(("delil ve sözleşme " * 200).strip())
    first = build_chunks(
        page_text=text,
        page_number=0,
        content_identity="a" * 64,
        provenance_state=LOW_PROVENANCE,
    )
    second = build_chunks(
        page_text=text,
        page_number=0,
        content_identity="a" * 64,
        provenance_state=LOW_PROVENANCE,
    )
    assert first == second
    assert len(first) > 1
    assert all(chunk.character_end > chunk.character_start for chunk in first)
    assert all(
        text[chunk.character_start : chunk.character_end] == chunk.text
        for chunk in first
    )


def test_pdf_parser_preserves_real_pages_and_block_offsets() -> None:
    document = fitz.open()
    first_page = document.new_page()
    first_page.insert_text((72, 72), "Davaci Ayse")
    second_page = document.new_page()
    second_page.insert_text((72, 72), "Delil sozlesmedir")
    pdf_bytes = document.tobytes()
    document.close()

    pages = parse_pdf_bytes(pdf_bytes)

    assert [page["page_number"] for page in pages] == [1, 2]
    assert "Davaci Ayse" in pages[0]["text_content"]
    assert "Delil sozlesmedir" in pages[1]["text_content"]
    for page in pages:
        for block in page["layout_data"]["blocks"]:
            assert (
                page["text_content"][block["character_start"] : block["character_end"]]
                == block["text"]
            )


def test_evidence_resolution_returns_real_chunk_page_and_span() -> None:
    page = ParsedPage(
        id="page-1",
        parsed_document_id="parsed-1",
        page_number=3,
        text_content="Tazminat talep eder.",
    )
    chunk = DocumentChunk(
        id="chunk-1",
        tenant_id="tenant-1",
        document_id="document-1",
        revision_id="revision-1",
        page_id=page.id,
        chunk_index=0,
        chunk_type="block",
        text_content=page.text_content,
        watermarked_text=page.text_content,
        character_start=10,
        character_end=31,
        provenance_state=VERIFIED_PDF,
    )

    resolved = resolve_evidence("talep eder", [(chunk, page)])

    assert resolved is not None
    assert resolved.chunk.id == "chunk-1"
    assert resolved.page.page_number == 3
    assert resolved.character_start == 19
    assert page.text_content[9:19] == resolved.evidence_text


@pytest.mark.asyncio
async def test_immutable_storage_rejects_conflicting_overwrite() -> None:
    service = StorageService()
    service.get_object_metadata = AsyncMock(
        return_value={"size": 3, "metadata": {"sha256": "old"}}
    )
    with pytest.raises(ImmutableObjectConflictError):
        await service.put_immutable_bytes(
            "immutable/key",
            b"new",
            sha256=hashlib.sha256(b"new").hexdigest(),
            mime_type="text/plain",
        )


@pytest.mark.asyncio
async def test_promotion_revalidates_the_exact_scanned_bytes() -> None:
    service = StorageService()
    service.get_object_metadata = AsyncMock(return_value=None)
    with pytest.raises(StorageIntegrityError):
        await service.promote_quarantine_object(
            "quarantine/key",
            "immutable/key",
            validated_body=b"changed",
            sha256=hashlib.sha256(b"original").hexdigest(),
            mime_type="application/pdf",
            size_bytes=len(b"original"),
        )


def scan_models(body: bytes) -> tuple[Document, DocumentRevision, dict]:
    digest = hashlib.sha256(body).hexdigest()
    document = Document(
        id="document-1",
        tenant_id="tenant-1",
        matter_id="matter-1",
        title="contract.pdf",
    )
    revision = DocumentRevision(
        id="revision-1",
        tenant_id="tenant-1",
        document_id=document.id,
        version=1,
        quarantine_key="quarantine/tenant-1/object.pdf",
        s3_key=None,
        is_canonical=False,
        file_hash=digest,
        size_bytes=len(body),
        mime_type="application/pdf",
        scan_status=DocumentState.SCANNING,
    )
    payload = {
        "tenant_id": "tenant-1",
        "matter_id": "matter-1",
        "document_id": document.id,
        "revision_id": revision.id,
        "s3_key": revision.quarantine_key,
        "expected_sha256": digest,
        "expected_size": len(body),
        "mime_type": revision.mime_type,
    }
    return document, revision, payload


@pytest.mark.asyncio
async def test_clean_scan_creates_canonical_revision_and_parse_job() -> None:
    body = b"%PDF-1.7 validated bytes"
    document, revision, payload = scan_models(body)
    session = AsyncMock()
    session.add = MagicMock()
    session.get.side_effect = lambda model, _: (
        revision if model is DocumentRevision else document
    )

    with (
        patch(
            "apps.worker.handlers.document.storage_service.get_object_bytes",
            AsyncMock(return_value=body),
        ),
        patch(
            "apps.worker.handlers.document.storage_service.promote_quarantine_object",
            AsyncMock(return_value=True),
        ) as promote,
        patch(
            "apps.worker.handlers.document.scan_with_clamav",
            AsyncMock(return_value=True),
        ),
    ):
        await handle_scan_document(payload, session)

    assert revision.is_canonical is True
    assert revision.scan_status == DocumentState.CLEAN
    assert revision.s3_key is not None and revision.file_hash in revision.s3_key
    promote.assert_awaited_once()
    queued = [call.args[0] for call in session.add.call_args_list]
    assert any(
        isinstance(item, Job) and item.type == "PARSE_DOCUMENT" for item in queued
    )


@pytest.mark.asyncio
async def test_infected_scan_never_creates_canonical_revision() -> None:
    body = b"%PDF-1.7 infected bytes"
    document, revision, payload = scan_models(body)
    session = AsyncMock()
    session.add = MagicMock()
    session.get.side_effect = lambda model, _: (
        revision if model is DocumentRevision else document
    )

    with (
        patch(
            "apps.worker.handlers.document.storage_service.get_object_bytes",
            AsyncMock(return_value=body),
        ),
        patch(
            "apps.worker.handlers.document.scan_with_clamav",
            AsyncMock(return_value=False),
        ),
    ):
        await handle_scan_document(payload, session)

    assert revision.is_canonical is False
    assert revision.s3_key is None
    assert revision.scan_status == DocumentState.INFECTED
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_changed_quarantine_bytes_are_terminally_rejected() -> None:
    body = b"%PDF-1.7 original"
    _, revision, payload = scan_models(body)
    changed = b"%PDF-1.7 changed"
    session = AsyncMock()
    session.get.side_effect = [revision, Document(id="document-1")]
    with (
        patch(
            "apps.worker.handlers.document.storage_service.get_object_bytes",
            AsyncMock(return_value=changed),
        ),
        pytest.raises(TerminalJobError, match="changed after validation"),
    ):
        await handle_scan_document(payload, session)
    assert revision.is_canonical is False
