import hashlib

import uuid6
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import DocumentAccessPolicy, MatterAccessPolicy
from apps.api.core.ratelimit import limiter
from apps.api.core.storage import storage_service
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.domain import MatterMember
from apps.api.models.parser import ParsedDocument
from apps.api.models.queue import Job
from apps.api.schemas.api import (
    DocumentResponse,
    DocumentViewerContextResponse,
    DownloadResponse,
    UploadCompleteResponse,
    UploadIntentRequest,
    UploadIntentResponse,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _document_response(
    document: Document, revision: DocumentRevision | None
) -> DocumentResponse:
    status = revision.scan_status.value if revision else "NO_REVISION"
    provenance_state = "PENDING_VERIFICATION"
    if revision and revision.scan_status == DocumentState.READY:
        provenance_state = (
            "VERIFIED_PDF"
            if revision.mime_type == "application/pdf"
            else "LOW_PROVENANCE"
        )
    return DocumentResponse(
        id=document.id,
        matter_id=document.matter_id,
        title=document.title,
        status=status,
        latest_revision_id=revision.id if revision else None,
        provenance_state=provenance_state,
        failure_reason=revision.failure_reason if revision else None,
        created_at=document.created_at,
    )


def _revision_provenance(revision: DocumentRevision) -> str:
    if not revision.is_canonical or revision.scan_status != DocumentState.READY:
        return "PENDING_VERIFICATION"
    return (
        "VERIFIED_PDF" if revision.mime_type == "application/pdf" else "LOW_PROVENANCE"
    )


@router.post(
    "/upload-intent",
    response_model=UploadIntentResponse,
    operation_id="createUploadIntent",
)
@limiter.limit("10/minute")
async def create_upload_intent(
    request: Request,
    payload: UploadIntentRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await DocumentAccessPolicy.can_upload(context, db, payload.matter_id)
    # Enforce file size limit (max 100MB per file as per Phase 10 rules)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    if payload.size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE} bytes.",
        )

    # Restrict allowed MIME types
    ALLOWED_MIMES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }
    if payload.mime_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {payload.mime_type}."
        )

    # 1. Create Parent Document
    doc = Document(
        tenant_id=context.tenant_id, matter_id=payload.matter_id, title=payload.filename
    )
    db.add(doc)
    await db.flush()  # get doc.id

    # 2. Create a provisional revision. It is not canonical until the exact
    # uploaded bytes pass validation and malware scanning.
    rev = DocumentRevision(
        tenant_id=context.tenant_id,
        document_id=doc.id,
        version=1,
        s3_key=None,
        size_bytes=payload.size_bytes,
        mime_type=payload.mime_type,
        scan_status=DocumentState.UPLOADING,
    )
    db.add(rev)
    await db.flush()  # get rev.id

    ext = ".pdf"
    if (
        payload.mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        ext = ".docx"
    elif payload.mime_type == "text/plain":
        ext = ".txt"

    quarantine_key = (
        f"quarantine/{context.tenant_id}/{payload.matter_id}/{uuid6.uuid7()}{ext}"
    )
    rev.quarantine_key = quarantine_key

    # 3. Generate presigned URL
    url = await storage_service.generate_presigned_upload_url(
        quarantine_key, payload.mime_type
    )

    await db.commit()

    return UploadIntentResponse(
        document_id=doc.id,
        revision_id=rev.id,
        presigned_url=url,
        storage_key=quarantine_key,
    )


@router.get(
    "/matters/{matter_id}",
    response_model=list[DocumentResponse],
    operation_id="listMatterDocuments",
)
@limiter.limit("60/minute")
async def list_matter_documents(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await DocumentAccessPolicy.can_read(context, db, matter_id)
    # Enforce RLS by tenant_id
    stmt = select(Document).where(
        Document.matter_id == matter_id, Document.tenant_id == context.tenant_id
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    res = []
    for d in docs:
        rev_res = await db.execute(
            select(DocumentRevision)
            .where(DocumentRevision.document_id == d.id)
            .order_by(DocumentRevision.version.desc())
        )
        latest_rev = rev_res.scalars().first()
        res.append(_document_response(d, latest_rev))
    return res


@router.get("", response_model=list[DocumentResponse], operation_id="listAllDocuments")
@limiter.limit("60/minute")
async def list_all_documents(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    MatterAccessPolicy.can_list(context)
    stmt = (
        select(Document)
        .join(
            MatterMember,
            (MatterMember.matter_id == Document.matter_id)
            & (MatterMember.user_id == context.principal_id),
        )
        .where(
            Document.tenant_id == context.tenant_id,
            MatterMember.tenant_id == context.tenant_id,
        )
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    res = []
    for d in docs:
        rev_res = await db.execute(
            select(DocumentRevision)
            .where(DocumentRevision.document_id == d.id)
            .order_by(DocumentRevision.version.desc())
        )
        latest_rev = rev_res.scalars().first()
        res.append(_document_response(d, latest_rev))
    return res


@router.get(
    "/{document_id}/viewer-context",
    response_model=DocumentViewerContextResponse,
    operation_id="getDocumentViewerContext",
)
@limiter.limit("60/minute")
async def get_document_viewer_context(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    document = await db.get(Document, document_id)
    if not document or document.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
    await DocumentAccessPolicy.can_read(context, db, document.matter_id)

    revision = await db.scalar(
        select(DocumentRevision)
        .where(
            DocumentRevision.document_id == document.id,
            DocumentRevision.tenant_id == context.tenant_id,
            DocumentRevision.is_canonical.is_(True),
        )
        .order_by(DocumentRevision.version.desc())
    )
    if revision is None:
        return DocumentViewerContextResponse(
            document=_document_response(document, None),
            revision=None,
            parsed_document=None,
        )

    parsed_document = await db.scalar(
        select(ParsedDocument)
        .where(
            ParsedDocument.document_id == document.id,
            ParsedDocument.revision_id == revision.id,
            ParsedDocument.tenant_id == context.tenant_id,
        )
        .order_by(ParsedDocument.parsing_revision.desc())
    )
    return DocumentViewerContextResponse(
        document=_document_response(document, revision),
        revision={
            "id": revision.id,
            "version": revision.version,
            "mime_type": revision.mime_type,
            "size_bytes": revision.size_bytes,
            "sha256": revision.file_hash,
            "immutable_at": revision.immutable_at,
            "scan_status": revision.scan_status.value,
            "provenance_state": _revision_provenance(revision),
        },
        parsed_document=(
            {
                "id": parsed_document.id,
                "revision_id": parsed_document.revision_id,
                "parser": parsed_document.parser_used,
                "parsing_revision": parsed_document.parsing_revision,
                "ocr_version": parsed_document.ocr_version,
                "pipeline_version": parsed_document.pipeline_version,
                "status": parsed_document.status,
                "provenance_state": parsed_document.provenance_state,
            }
            if parsed_document
            else None
        ),
    )


@router.get(
    "/{document_id}", response_model=DocumentResponse, operation_id="getDocument"
)
@limiter.limit("60/minute")
async def get_document(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, document_id)
    if not doc or doc.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
    await DocumentAccessPolicy.can_read(context, db, doc.matter_id)

    rev_res = await db.execute(
        select(DocumentRevision)
        .where(DocumentRevision.document_id == doc.id)
        .order_by(DocumentRevision.version.desc())
    )
    latest_rev = rev_res.scalars().first()
    return _document_response(doc, latest_rev)


@router.post(
    "/{document_id}/complete",
    operation_id="completeUpload",
    response_model=UploadCompleteResponse,
)
@limiter.limit("30/minute")
async def complete_upload(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    # Verify document exists and belongs to tenant
    doc = await db.get(Document, document_id)
    if not doc or doc.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")

    await DocumentAccessPolicy.can_upload(context, db, doc.matter_id)

    result = await db.execute(
        select(DocumentRevision)
        .where(DocumentRevision.document_id == document_id)
        .order_by(DocumentRevision.version.desc())
    )
    rev = result.scalars().first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    if rev.scan_status == DocumentState.UPLOADING:
        if not rev.quarantine_key or rev.is_canonical:
            raise HTTPException(status_code=409, detail="Invalid upload revision state")
        meta = await storage_service.get_object_metadata(rev.quarantine_key)
        if not meta or meta["size"] == 0:
            raise HTTPException(
                status_code=400, detail="Uploaded file not found in storage or is empty"
            )

        if meta["size"] > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")

        if rev.size_bytes is not None and meta["size"] != rev.size_bytes:
            rev.scan_status = DocumentState.QUARANTINED
            rev.failure_reason = "Uploaded size does not match the upload intent"
            await db.commit()
            raise HTTPException(
                status_code=400, detail="Uploaded size does not match upload intent"
            )

        file_bytes = await storage_service.get_object_bytes(rev.quarantine_key)
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Could not read file data from storage"
            )

        import io
        import zipfile

        import fitz

        # MIME Sniffing & Extension mismatch
        actual_mime = "application/octet-stream"
        if file_bytes.startswith(b"%PDF-"):
            actual_mime = "application/pdf"
        elif file_bytes.startswith(b"PK\x03\x04"):
            actual_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            try:
                # If it's valid UTF-8 and we expect text/plain, accept it
                file_bytes.decode("utf-8")
                actual_mime = "text/plain"
            except UnicodeDecodeError:
                pass

        if actual_mime != rev.mime_type:
            rev.scan_status = DocumentState.QUARANTINED
            rev.failure_reason = "Declared and detected MIME types differ"
            await db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"MIME type mismatch: declared {rev.mime_type}, detected {actual_mime}",
            )

        # ZIP bomb and nested archive check for DOCX (which is a ZIP)
        if (
            actual_mime
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    total_uncompressed = 0
                    for info in z.infolist():
                        if info.filename.lower().endswith(
                            (
                                ".zip",
                                ".rar",
                                ".7z",
                                ".exe",
                                ".bat",
                                ".cmd",
                                ".js",
                                ".vbs",
                            )
                        ):
                            rev.scan_status = DocumentState.QUARANTINED
                            rev.failure_reason = (
                                "Nested archive or executable content in DOCX"
                            )
                            await db.commit()
                            raise HTTPException(
                                status_code=400,
                                detail="Nested archives or executable scripts found in DOCX",
                            )
                        total_uncompressed += info.file_size

                    compression_ratio = total_uncompressed / max(len(file_bytes), 1)
                    if compression_ratio > 100:  # arbitrary threshold for zip bomb
                        rev.scan_status = DocumentState.QUARANTINED
                        rev.failure_reason = "Potential DOCX decompression bomb"
                        await db.commit()
                        raise HTTPException(
                            status_code=400, detail="Potential ZIP bomb detected"
                        )
            except zipfile.BadZipFile:
                rev.scan_status = DocumentState.QUARANTINED
                rev.failure_reason = "Invalid DOCX container"
                await db.commit()
                raise HTTPException(status_code=400, detail="Invalid ZIP/DOCX format")

        # PDF active content risk check
        if actual_mime == "application/pdf":
            try:
                pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                # Look for JS or OpenAction
                # Simplified check for /JS or /JavaScript using fitz xrefs
                for i in range(1, pdf_doc.xref_length()):
                    xref_str = pdf_doc.xref_object(i)
                    if (
                        "/JS " in xref_str
                        or "/JavaScript" in xref_str
                        or "/OpenAction" in xref_str
                    ):
                        rev.scan_status = DocumentState.QUARANTINED
                        rev.failure_reason = "Active content in PDF"
                        await db.commit()
                        raise HTTPException(
                            status_code=400,
                            detail="Active content (JavaScript/OpenAction) detected in PDF",
                        )
            except Exception as e:
                if isinstance(e, HTTPException):
                    raise
                rev.scan_status = DocumentState.QUARANTINED
                rev.failure_reason = "PDF security parsing failed"
                await db.commit()
                raise HTTPException(
                    status_code=400, detail="Failed to parse PDF for security check"
                )

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        dup_res = await db.execute(
            select(DocumentRevision)
            .join(DocumentRevision.document)
            .where(
                Document.tenant_id == context.tenant_id,
                Document.matter_id == doc.matter_id,
                DocumentRevision.file_hash == sha256_hash,
                DocumentRevision.id != rev.id,
            )
        )
        existing_dup = dup_res.scalars().first()
        if existing_dup:
            rev.scan_status = DocumentState.BLOCKED
            rev.failure_reason = "Duplicate content in this matter"
            await db.commit()
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate document detected: identical content exists in revision {existing_dup.id}",
            )

        rev.file_hash = sha256_hash
        rev.size_bytes = meta["size"]
        rev.scan_status = DocumentState.SCANNING

        # 11. ClamAV scan job
        job = Job(
            type="SCAN_DOCUMENT",
            tenant_id=context.tenant_id,
            matter_id=doc.matter_id,
            requested_by=context.principal_id,
            idempotency_key=f"scan:{rev.id}:{sha256_hash}",
            payload={
                "document_id": doc.id,
                "revision_id": rev.id,
                "s3_key": rev.quarantine_key,
                "expected_sha256": sha256_hash,
                "expected_size": meta["size"],
                "mime_type": rev.mime_type,
                "matter_id": doc.matter_id,
            },
        )
        db.add(job)

        # 12. Operation record
        from apps.api.models.review import AuditLog

        op_log = AuditLog(
            tenant_id=context.tenant_id,
            user_id=context.principal_id,
            action="UPLOAD_DOCUMENT",
            entity_type="document_revision",
            entity_id=rev.id,
            details={"status": "scanning", "file_hash": sha256_hash},
        )
        db.add(op_log)

        # 13. Outbox event
        from apps.api.models.domain import MatterEvent

        outbox = MatterEvent(
            tenant_id=context.tenant_id,
            matter_id=doc.matter_id,
            event_type="DOCUMENT_UPLOADED",
            description=f"Document {doc.title} uploaded for scanning.",
            event_date=rev.created_at,
        )
        db.add(outbox)

        await db.commit()

    return {"status": rev.scan_status.value, "revision_id": rev.id}


@router.get(
    "/{document_id}/download",
    operation_id="downloadDocument",
    response_model=DownloadResponse,
)
@limiter.limit("60/minute")
async def download_document(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, document_id)
    if not doc or doc.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
    await DocumentAccessPolicy.can_read(context, db, doc.matter_id)

    result = await db.execute(
        select(DocumentRevision)
        .where(DocumentRevision.document_id == document_id)
        .order_by(DocumentRevision.version.desc())
    )
    rev = result.scalars().first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    if rev.scan_status == DocumentState.INFECTED:
        raise HTTPException(
            status_code=403, detail="Document is infected and cannot be downloaded"
        )
    elif not rev.is_canonical or rev.s3_key is None:
        raise HTTPException(status_code=425, detail="Document is still being scanned")

    url = await storage_service.generate_presigned_download_url(rev.s3_key)
    return {"presigned_url": url, "expires_in_seconds": 300}
