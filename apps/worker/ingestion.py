import hashlib
from typing import Any

from apps.api.core.storage import storage_service
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.parser import DocumentChunk, ParsedDocument, ParsedPage
from apps.api.models.queue import Job
from apps.worker.provenance import CHUNKING_VERSION, build_chunks, normalize_text
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def persist_parsed_pages(
    session: AsyncSession,
    *,
    document: Document,
    revision: DocumentRevision,
    pages: list[dict[str, Any]],
    parser_used: str,
    provenance_state: str,
    ocr_version: str | None = None,
) -> ParsedDocument:
    if not revision.is_canonical or not revision.s3_key or not revision.file_hash:
        raise ValueError("Cannot parse a non-canonical document revision")

    normalized_pages: list[dict[str, Any]] = []
    for page in pages:
        page_text = normalize_text(str(page.get("text", "")))
        if not page_text:
            continue
        normalized_pages.append(
            {
                "page_number": int(page["page_number"]),
                "text": page_text,
                "layout": page.get("layout") or {},
            }
        )
    if not normalized_pages:
        raise ValueError("Parser produced no citable text")

    canonical_text = "\n\f\n".join(page["text"] for page in normalized_pages)
    output_hash = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    existing = await session.scalar(
        select(ParsedDocument)
        .where(
            ParsedDocument.revision_id == revision.id,
            ParsedDocument.output_hash == output_hash,
        )
        .order_by(ParsedDocument.parsing_revision.desc())
        .limit(1)
    )
    if existing is not None:
        return existing

    latest_run = await session.scalar(
        select(func.max(ParsedDocument.parsing_revision)).where(
            ParsedDocument.revision_id == revision.id
        )
    )
    parsed_document = ParsedDocument(
        tenant_id=document.tenant_id,
        document_id=document.id,
        revision_id=revision.id,
        parsing_revision=int(latest_run or 0) + 1,
        parser_used=parser_used,
        ocr_version=ocr_version,
        pipeline_version=CHUNKING_VERSION,
        input_hash=revision.file_hash,
        output_hash=output_hash,
        provenance_state=provenance_state,
        status="COMPLETED",
    )
    session.add(parsed_document)
    await session.flush()

    for page in normalized_pages:
        parsed_page = ParsedPage(
            parsed_document_id=parsed_document.id,
            page_number=page["page_number"],
            text_content=page["text"],
            layout_data=page["layout"],
        )
        session.add(parsed_page)
        await session.flush()

        layout_blocks = page["layout"].get("blocks") or None
        chunks = build_chunks(
            page_text=page["text"],
            page_number=page["page_number"],
            content_identity=revision.file_hash,
            provenance_state=provenance_state,
            layout_blocks=layout_blocks,
        )
        for chunk in chunks:
            session.add(
                DocumentChunk(
                    id=chunk.id,
                    tenant_id=document.tenant_id,
                    document_id=document.id,
                    revision_id=revision.id,
                    page_id=parsed_page.id,
                    chunk_index=chunk.chunk_index,
                    chunk_type="block" if chunk.bbox else "text_span",
                    text_content=chunk.text,
                    watermarked_text=(f"{chunk.text}\n[MESA_SOURCE_CHUNK:{chunk.id}]"),
                    character_start=chunk.character_start,
                    character_end=chunk.character_end,
                    content_sha256=chunk.content_sha256,
                    extraction_version=CHUNKING_VERSION,
                    provenance_state=chunk.provenance_state,
                    bbox=chunk.bbox,
                )
            )

    artifact_key = (
        f"immutable/{document.tenant_id}/{document.matter_id}/{document.id}/"
        f"{revision.id}/parsed/{output_hash}.txt"
    )
    await storage_service.put_immutable_bytes(
        artifact_key,
        canonical_text.encode("utf-8"),
        sha256=output_hash,
        mime_type="text/plain; charset=utf-8",
    )

    revision.scan_status = DocumentState.EXTRACTION_PENDING
    session.add(
        Job(
            type="EXTRACT_LEGAL_DATA",
            tenant_id=document.tenant_id,
            matter_id=document.matter_id,
            idempotency_key=f"extract:{parsed_document.id}",
            payload={
                "parsed_document_id": parsed_document.id,
                "matter_id": document.matter_id,
            },
        )
    )
    return parsed_document
