import hashlib

import fitz
import pytest
import uuid6
from apps.api.core.database import AsyncSessionLocal
from apps.api.core.rls import reset_tenant_id, set_tenant_id
from apps.api.core.utils import utc_now
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.domain import Firm, Matter
from apps.api.models.parser import ParsedDocument, ParsedPage
from apps.worker.parsers.pdf import PyMuPDFParser
from sqlalchemy import func, select, text


def create_dummy_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello MESA Law! This is a test document.")
    return doc.write()


@pytest.mark.asyncio
async def test_pdf_parsing_and_fts():
    pdf_bytes = create_dummy_pdf()

    # 1. Test the parser itself
    parser = PyMuPDFParser()
    pages = []
    async for page in parser.parse(pdf_bytes):
        pages.append(page)

    assert len(pages) == 1
    assert "MESA Law" in pages[0]["text_content"]
    assert "blocks" in pages[0]["layout_data"]

    # 2. Test saving to DB and FTS
    tenant_id = str(uuid6.uuid7())
    tenant_token = set_tenant_id(tenant_id)

    try:
        async with AsyncSessionLocal() as db:
            firm = Firm(id=tenant_id, name="Test Firm")
            db.add(firm)
            await db.flush()

            matter = Matter(title="Test Matter", tenant_id=tenant_id)
            db.add(matter)
            await db.flush()

            doc = Document(matter_id=matter.id, title="Test Doc", tenant_id=tenant_id)
            db.add(doc)
            await db.flush()

            rev = DocumentRevision(
                tenant_id=tenant_id,
                document_id=doc.id,
                s3_key=f"test/{uuid6.uuid7()}.pdf",
                mime_type="application/pdf",
                is_canonical=True,
                file_hash=hashlib.sha256(pdf_bytes).hexdigest(),
                immutable_at=utc_now(),
                scan_status=DocumentState.READY,
            )
            db.add(rev)
            await db.flush()

            parsed_doc = ParsedDocument(
                document_id=doc.id,
                revision_id=rev.id,
                parser_used="pymupdf",
                tenant_id=tenant_id,
            )
            db.add(parsed_doc)
            await db.flush()

            parsed_page = ParsedPage(
                parsed_document_id=parsed_doc.id,
                page_number=pages[0]["page_number"],
                text_content=pages[0]["text_content"],
                layout_data=pages[0]["layout_data"],
            )
            db.add(parsed_page)
            await db.flush()

            await db.execute(
                text(
                    "UPDATE parsed_pages SET fts_vector = to_tsvector('english', :text) WHERE id = :pid"
                ).bindparams(text=parsed_page.text_content, pid=parsed_page.id)
            )
            await db.commit()

        # 3. Test searching using FTS
        async with AsyncSessionLocal() as db:
            stmt = select(ParsedPage).where(
                ParsedPage.fts_vector.op("@@")(func.plainto_tsquery("english", "MESA"))
            )
            result = await db.execute(stmt)
            found_pages = result.scalars().all()

            assert len(found_pages) >= 1
            assert any("MESA Law" in p.text_content for p in found_pages)
    finally:
        reset_tenant_id(tenant_token)
