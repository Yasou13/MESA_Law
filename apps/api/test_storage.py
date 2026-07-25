import pytest
import uuid6
from apps.api.core.storage import storage_service
from apps.api.models.document import Document, DocumentRevision
from apps.api.core.database import AsyncSessionLocal
from apps.api.core.rls import set_tenant_id
from apps.api.models.domain import Firm, Matter

@pytest.mark.asyncio
async def test_presigned_url_generation():
    key = "test-tenant/matter-123/doc.pdf"
    
    url = await storage_service.generate_presigned_upload_url(key, "application/pdf")
    assert url is not None
    assert "http://" in url
    assert "mesa-law-docs" in url
    assert "X-Amz-Credential" in url or "AWSAccessKeyId" in url

@pytest.mark.asyncio
async def test_document_revision_model():
    tenant_id = str(uuid6.uuid7())
    
    async with AsyncSessionLocal() as session:
        set_tenant_id(tenant_id)
        
        firm = Firm(id=tenant_id, name="Test Firm")
        session.add(firm)
        await session.flush()
        
        matter = Matter(title="Test Matter", tenant_id=tenant_id)
        session.add(matter)
        await session.flush()
        
        doc = Document(matter_id=matter.id, title="Initial Brief", tenant_id=tenant_id)
        session.add(doc)
        await session.flush()
        
        # Test immutable key requirement
        rev1_key = f"{tenant_id}/{matter.id}/{uuid6.uuid7()}.pdf"
        rev = DocumentRevision(
            document_id=doc.id,
            s3_key=rev1_key,
            mime_type="application/pdf",
            scan_status="uploading"
        )
        session.add(rev)
        await session.commit()
        
        # Verify
        rev_fetched = await session.get(DocumentRevision, rev.id)
        assert rev_fetched.version == 1
        assert rev_fetched.s3_key == rev1_key
        assert rev_fetched.scan_status == "uploading"
