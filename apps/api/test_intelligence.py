import hashlib

import pytest
import uuid6
from apps.api.adapters.mock_intelligence import MockMesaAdapter
from apps.api.adapters.pg_intelligence import PostgresLexicalAdapter
from apps.api.core.database import AsyncSessionLocal
from apps.api.core.ports.intelligence import IntelligenceQuery, OperationState
from apps.api.core.rls import reset_tenant_id, set_tenant_id
from apps.api.core.utils import utc_now
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.domain import Firm, Matter
from apps.api.models.parser import ParsedDocument, ParsedPage
from sqlalchemy import text


@pytest.fixture
def mock_adapter():
    return MockMesaAdapter()


@pytest.mark.asyncio
async def test_mock_adapter_fixtures(mock_adapter):
    query = IntelligenceQuery(tenant_id="test", query_text="please test pending status")
    res = await mock_adapter.query(query)
    assert res.state == OperationState.pending

    query = IntelligenceQuery(tenant_id="test", query_text="normal query")
    res = await mock_adapter.query(query)
    assert res.state == OperationState.success
    assert len(res.evidence) == 1


@pytest.mark.asyncio
async def test_pg_lexical_adapter():
    tenant_id = str(uuid6.uuid7())
    tenant_token = set_tenant_id(tenant_id)
    chunk_text = "This document contains crucial evidence about the contract dispute."

    try:
        async with AsyncSessionLocal() as db:
            firm = Firm(id=tenant_id, name="Test Firm")
            db.add(firm)
            matter = Matter(title="Intelligence Matter", tenant_id=tenant_id)
            db.add(matter)
            await db.flush()

            doc = Document(matter_id=matter.id, title="Doc 1", tenant_id=tenant_id)
            db.add(doc)
            await db.flush()

            rev = DocumentRevision(
                tenant_id=tenant_id,
                document_id=doc.id,
                s3_key=f"test/{uuid6.uuid7()}.pdf",
                mime_type="application/pdf",
                is_canonical=True,
                file_hash=hashlib.sha256(chunk_text.encode()).hexdigest(),
                immutable_at=utc_now(),
                scan_status=DocumentState.READY,
            )
            db.add(rev)
            await db.flush()

            parsed_doc = ParsedDocument(
                document_id=doc.id,
                revision_id=rev.id,
                parser_used="test",
                tenant_id=tenant_id,
                provenance_state="VERIFIED_PDF_TEXT",
            )
            db.add(parsed_doc)
            await db.flush()

            parsed_page = ParsedPage(
                parsed_document_id=parsed_doc.id,
                page_number=1,
                text_content=chunk_text,
            )
            db.add(parsed_page)
            await db.flush()

            from apps.api.models.parser import DocumentChunk

            chunk = DocumentChunk(
                tenant_id=tenant_id,
                document_id=doc.id,
                revision_id=rev.id,
                page_id=parsed_page.id,
                chunk_index=0,
                text_content=chunk_text,
                watermarked_text=chunk_text,
                character_start=0,
                character_end=len(chunk_text),
                content_sha256=hashlib.sha256(chunk_text.encode()).hexdigest(),
                extraction_version="test-v1",
                provenance_state="VERIFIED_PDF_TEXT",
            )
            db.add(chunk)
            await db.flush()

            await db.execute(
                text(
                    "UPDATE document_chunks SET fts_vector = to_tsvector('turkish', :text) WHERE id = :cid"
                ).bindparams(text=chunk.text_content, cid=chunk.id)
            )
            await db.commit()

        # Test PG Adapter
        async with AsyncSessionLocal() as db:
            pg_adapter = PostgresLexicalAdapter(session=db)

            q1 = IntelligenceQuery(
                tenant_id=tenant_id, query_text="crucial evidence", matter_id=matter.id
            )
            r1 = await pg_adapter.query(q1)
            assert r1.state == OperationState.success
            assert len(r1.evidence) == 1
            assert "crucial evidence" in r1.evidence[0].text_snippet
            assert r1.evidence[0].page_number == 1
            assert r1.evidence[0].revision_id == rev.id
            assert r1.evidence[0].chunk_id == chunk.id

            q2 = IntelligenceQuery(tenant_id=tenant_id, query_text="apples and oranges")
            r2 = await pg_adapter.query(q2)
            assert r2.state == OperationState.no_evidence_retrieved
    finally:
        reset_tenant_id(tenant_token)
