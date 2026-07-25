
import os
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
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models.queue import Job

from apps.api.core.ratelimit import limiter

router = APIRouter()

@router.post("/upload-intent", response_model=UploadIntentResponse, operation_id="createUploadIntent")
@limiter.limit("10/minute")
async def create_upload_intent(
    request: Request,
    req: UploadIntentRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    doc = Document(matter_id=req.matter_id, title=req.filename, tenant_id=context.tenant_id)
    db.add(doc)
    await db.flush()
    
    ext = os.path.splitext(req.filename)[1].lower() if req.filename else ""
    uuid_str = str(uuid6.uuid7())
    s3_key = f"{context.tenant_id}/{req.matter_id}/{uuid_str}{ext}"
    
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
@limiter.limit("100/minute")
async def list_documents(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.matter_id == matter_id, Document.tenant_id == context.tenant_id))
    docs = result.scalars().all()
    
    res = []
    for d in docs:
        rev_res = await db.execute(select(DocumentRevision).where(DocumentRevision.document_id == d.id).order_by(DocumentRevision.version.desc()))
        latest_rev = rev_res.scalars().first()
        status = latest_rev.scan_status if latest_rev else "clean"
        res.append({"id": d.id, "title": d.title, "status": status})
    return res

@router.post("/{document_id}/complete", operation_id="completeUpload")
@limiter.limit("30/minute")
async def complete_upload(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Verify document exists and belongs to tenant
    doc = await db.get(Document, document_id)
    if not doc or doc.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    result = await db.execute(select(DocumentRevision).where(DocumentRevision.document_id == document_id).order_by(DocumentRevision.version.desc()))
    rev = result.scalars().first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
        
    if rev.scan_status == "uploading":
        meta = await storage_service.get_object_metadata(rev.s3_key)
        if not meta or meta["size"] == 0:
            raise HTTPException(status_code=400, detail="Uploaded file not found in storage or is empty")
            
        rev.scan_status = "scanning"
        # Queue the scanning job
        job = Job(
            type="SCAN_DOCUMENT",
            payload={"document_id": doc.id, "revision_id": rev.id, "s3_key": rev.s3_key}
        )
        db.add(job)
        await db.commit()
    
    return {"status": "scanning", "revision_id": rev.id}

@router.get("/{document_id}/download", operation_id="downloadDocument")
@limiter.limit("60/minute")
async def download_document(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, document_id)
    if not doc or doc.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    result = await db.execute(select(DocumentRevision).where(DocumentRevision.document_id == document_id).order_by(DocumentRevision.version.desc()))
    rev = result.scalars().first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
        
    if rev.scan_status == "infected":
        raise HTTPException(status_code=403, detail="Document is infected and cannot be downloaded")
    elif rev.scan_status != "clean":
        # For development flexibility, we might allow downloading un-scanned docs, 
        # but strict policy: wait for scan
        raise HTTPException(status_code=425, detail="Document is still being scanned")
        
    url = await storage_service.generate_presigned_download_url(rev.s3_key)
    return {"presigned_url": url}
