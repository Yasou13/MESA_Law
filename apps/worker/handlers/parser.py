import asyncio
import hashlib
import logging
import os
import tempfile

import docx2txt
from apps.api.core.storage import storage_service
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.queue import Job
from apps.worker.ingestion import persist_parsed_pages
from apps.worker.jobs import TerminalJobError
from apps.worker.parsers.pdf import PyMuPDFParser
from apps.worker.provenance import LOW_PROVENANCE, VERIFIED_PDF, normalize_text
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.parser")


async def handle_parse_document(payload: dict, session: AsyncSession) -> None:
    document_id = payload.get("document_id")
    revision_id = payload.get("revision_id")
    object_key = payload.get("s3_key")
    if not document_id or not revision_id or not object_key:
        raise TerminalJobError("Missing required parse payload fields")

    document = await session.get(Document, document_id)
    revision = await session.get(DocumentRevision, revision_id)
    if document is None:
        raise TerminalJobError(f"Document {document_id} not found")
    if revision is None or revision.document_id != document.id:
        raise TerminalJobError(
            f"Revision {revision_id} does not belong to document {document_id}"
        )
    if not revision.is_canonical or revision.s3_key != object_key:
        raise TerminalJobError("Only the immutable canonical revision may be parsed")

    file_bytes = await storage_service.get_object_bytes(
        object_key, max_bytes=100 * 1024 * 1024 + 1
    )
    if not file_bytes or len(file_bytes) > 100 * 1024 * 1024:
        raise TerminalJobError("Canonical document bytes are missing or oversized")
    if hashlib.sha256(file_bytes).hexdigest() != revision.file_hash:
        raise TerminalJobError("Canonical document hash verification failed")

    revision.scan_status = DocumentState.PARSING
    pages: list[dict] = []
    parser_used: str
    provenance_state: str

    if revision.mime_type == "application/pdf":
        parser_used = "pymupdf-exact-v2"
        provenance_state = VERIFIED_PDF
        pdf_parser = PyMuPDFParser()
        extracted_pages = [page async for page in pdf_parser.parse(file_bytes)]
        if any(page["layout_data"].get("ocr_required") for page in extracted_pages):
            revision.scan_status = DocumentState.OCR_REQUIRED
            session.add(
                Job(
                    type="OCR_DOCUMENT",
                    tenant_id=document.tenant_id,
                    matter_id=document.matter_id,
                    idempotency_key=f"ocr:{revision.id}:{revision.file_hash}",
                    payload={
                        "document_id": document.id,
                        "revision_id": revision.id,
                        "s3_key": revision.s3_key,
                        "matter_id": document.matter_id,
                    },
                )
            )
            return
        pages = [
            {
                "page_number": page["page_number"],
                "text": page["text_content"],
                "layout": page["layout_data"],
            }
            for page in extracted_pages
        ]
    elif (
        revision.mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        parser_used = "docx2txt-v0.9"
        provenance_state = LOW_PROVENANCE
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_bytes)
        try:
            extracted_text = await asyncio.to_thread(docx2txt.process, temp_path)
        finally:
            os.remove(temp_path)
        pages = [
            {
                "page_number": 0,
                "text": normalize_text(extracted_text),
                "layout": {"page_unavailable": True, "blocks": []},
            }
        ]
    elif revision.mime_type == "text/plain":
        parser_used = "utf8-text-v1"
        provenance_state = LOW_PROVENANCE
        try:
            extracted_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TerminalJobError("Text document is not valid UTF-8") from exc
        pages = [
            {
                "page_number": 0,
                "text": normalize_text(extracted_text),
                "layout": {"page_unavailable": True, "blocks": []},
            }
        ]
    else:
        raise TerminalJobError(f"Unsupported canonical MIME type: {revision.mime_type}")

    await session.execute(
        text(
            "UPDATE draft_citations SET verification_state = 'STALE_REVISION' "
            "WHERE document_id = :doc_id "
            "AND document_revision_id != :new_rev "
            "AND verification_state != 'STALE_REVISION'"
        ),
        {"doc_id": document_id, "new_rev": revision_id},
    )
    await persist_parsed_pages(
        session,
        document=document,
        revision=revision,
        pages=pages,
        parser_used=parser_used,
        provenance_state=provenance_state,
    )
    logger.info("Parsed immutable revision %s with %s", revision.id, parser_used)
