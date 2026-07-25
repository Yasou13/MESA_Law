
import uuid6
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.storage import storage_service
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.document import Document, DocumentRevision
from apps.api.schemas.api import (
    DocumentResponse,
    UploadIntentRequest,
    UploadIntentResponse,
)
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/upload-intent", response_model=UploadIntentResponse, operation_id="createUploadIntent")
async def create_upload_intent(
    req: UploadIntentRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    doc = Document(matter_id=req.matter_id, title=req.filename, tenant_id=context.tenant_id)
    db.add(doc)
    await db.flush()
    
    uuid_str = str(uuid6.uuid7())
    s3_key = f"{context.tenant_id}/{req.matter_id}/{uuid_str}"
    
    rev = DocumentRevision(
        document_id=doc.id,
        s3_key=s3_key,
        mime_type=req.mime_type,
        scan_status="uploading"
    )
    db.add(rev)
    await db.commit()
    
    url = await storage_service.generate_presigned_upload_url(s3_key, req.mime_type)
    
    return {
        "document_id": doc.id,
        "revision_id": rev.id,
        "presigned_url": url
    }

@router.get("/matter/{matter_id}", response_model=list[DocumentResponse], operation_id="listDocuments")
async def list_documents(
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.matter_id == matter_id, Document.tenant_id == context.tenant_id))
    docs = result.scalars().all()
    return [{"id": d.id, "title": d.title} for d in docs]
