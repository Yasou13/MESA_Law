import os
import uuid6
import hashlib
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
    payload: UploadIntentRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Enforce file size limit (max 100MB per file as per Phase 10 rules)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    if payload.size_bytes > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE} bytes.")

    # Restrict allowed MIME types
    ALLOWED_MIMES = {
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
        "image/jpeg", 
        "image/png"
    }
    if payload.mime_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {payload.mime_type}.")

    # Generate immutable storage key
    file_uuid = uuid6.uuid7()
    ext = ".pdf"
    if payload.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        ext = ".docx"
    elif payload.mime_type == "image/jpeg":
        ext = ".jpg"
    elif payload.mime_type == "image/png":
        ext = ".png"
        
    s3_key = f"{context.tenant_id}/{payload.matter_id}/{file_uuid}{ext}"
    
    # 1. Create Parent Document
    doc = Document(
        tenant_id=context.tenant_id,
        matter_id=payload.matter_id,
        title=payload.filename
    )
    db.add(doc)
    await db.flush() # get doc.id
    
    # 2. Create Initial Revision (Quarantine State: uploading)
    rev = DocumentRevision(
        document_id=doc.id,
        version=1,
        s3_key=s3_key,
        size_bytes=payload.size_bytes,
        mime_type=payload.mime_type,
        scan_status="uploading"
    )
    db.add(rev)
    
    # 3. Generate presigned URL
    url = await storage_service.generate_presigned_upload_url(s3_key, payload.mime_type)
    
    await db.commit()
    
    return UploadIntentResponse(
        document_id=doc.id,
        revision_id=rev.id,
        upload_url=url,
        storage_key=s3_key
    )

@router.get("/matters/{matter_id}", response_model=list[DocumentResponse], operation_id="listMatterDocuments")
@limiter.limit("60/minute")
async def list_matter_documents(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Enforce RLS by tenant_id
    stmt = select(Document).where(Document.matter_id == matter_id, Document.tenant_id == context.tenant_id)
    result = await db.execute(stmt)
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
            
        if meta["size"] > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
            
        file_bytes = await storage_service.get_object_bytes(rev.s3_key)
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Could not read file data from storage")
            
        if file_bytes.startswith(b"MZ") or file_bytes.startswith(b"\x7fELF") or file_bytes.startswith(b"#!"):
            raise HTTPException(status_code=400, detail="Executable or script files are strictly prohibited")
            
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        
        dup_res = await db.execute(
            select(DocumentRevision)
            .join(DocumentRevision.document)
            .where(
                Document.tenant_id == context.tenant_id,
                Document.matter_id == doc.matter_id,
                DocumentRevision.file_hash == sha256_hash,
                DocumentRevision.id != rev.id
            )
        )
        existing_dup = dup_res.scalars().first()
        if existing_dup:
            raise HTTPException(status_code=409, detail=f"Duplicate document detected: identical content exists in revision {existing_dup.id}")
            
        rev.file_hash = sha256_hash
        rev.size_bytes = meta["size"]
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
