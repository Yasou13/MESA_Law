import asyncio
import hashlib
import io
import logging

import fitz
import pytesseract
from apps.api.core.storage import storage_service
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.worker.ingestion import persist_parsed_pages
from apps.worker.jobs import TerminalJobError
from apps.worker.parsers.pdf import parse_pdf_bytes
from apps.worker.provenance import VERIFIED_PDF_OCR, normalize_text
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.ocr")


def _ocr_missing_pages(pdf_bytes: bytes, extracted_pages: list[dict]) -> list[dict]:
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pages: list[dict] = []
        for index, extracted in enumerate(extracted_pages):
            if extracted["text_content"]:
                pages.append(
                    {
                        "page_number": extracted["page_number"],
                        "text": extracted["text_content"],
                        "layout": extracted["layout_data"],
                    }
                )
                continue

            pixmap = document[index].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            ocr_text = normalize_text(
                pytesseract.image_to_string(image, lang="tur+eng")
            )
            if not ocr_text:
                raise TerminalJobError(f"OCR produced no text for PDF page {index + 1}")
            pages.append(
                {
                    "page_number": index + 1,
                    "text": ocr_text,
                    "layout": {
                        "blocks": [],
                        "ocr_used": True,
                        "ocr_version": "tesseract-5",
                        "bbox_unavailable": True,
                    },
                }
            )
        return pages
    finally:
        document.close()


async def handle_ocr_document(payload: dict, session: AsyncSession) -> None:
    document_id = payload.get("document_id")
    revision_id = payload.get("revision_id")
    object_key = payload.get("s3_key")
    if not document_id or not revision_id or not object_key:
        raise TerminalJobError("Missing required OCR payload fields")

    document = await session.get(Document, document_id)
    revision = await session.get(DocumentRevision, revision_id)
    if document is None:
        raise TerminalJobError(f"Document {document_id} not found for OCR")
    if revision is None or revision.document_id != document.id:
        raise TerminalJobError(
            f"Revision {revision_id} does not belong to document {document_id}"
        )
    if (
        revision.mime_type != "application/pdf"
        or not revision.is_canonical
        or revision.s3_key != object_key
    ):
        raise TerminalJobError("OCR requires an immutable canonical PDF revision")

    pdf_bytes = await storage_service.get_object_bytes(
        object_key, max_bytes=100 * 1024 * 1024 + 1
    )
    if not pdf_bytes or len(pdf_bytes) > 100 * 1024 * 1024:
        raise TerminalJobError("Canonical PDF bytes are missing or oversized")
    if hashlib.sha256(pdf_bytes).hexdigest() != revision.file_hash:
        raise TerminalJobError("Canonical PDF hash verification failed before OCR")

    revision.scan_status = DocumentState.OCR_RUNNING
    try:
        extracted_pages = await asyncio.to_thread(parse_pdf_bytes, pdf_bytes)
        pages = await asyncio.to_thread(_ocr_missing_pages, pdf_bytes, extracted_pages)
    except TerminalJobError:
        raise
    except Exception as exc:
        raise TerminalJobError(f"OCR engine failed: {exc}") from exc

    await persist_parsed_pages(
        session,
        document=document,
        revision=revision,
        pages=pages,
        parser_used="pymupdf+tesseract-exact-v2",
        provenance_state=VERIFIED_PDF_OCR,
        ocr_version="tesseract-5",
    )
    logger.info("OCR completed for immutable revision %s", revision.id)
