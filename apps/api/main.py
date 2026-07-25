from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import uuid6

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.errors import ProblemException, problem_exception_handler, global_exception_handler
from apps.api.core.middleware import TraceMiddleware
from apps.api.core.security import verify_csrf, get_current_user
from apps.api.core.rls import set_tenant_id
from apps.api.routers import firms, matters, documents, parser, reviews
from apps.api.models.domain import Firm, Matter
from apps.api.models.document import Document, DocumentRevision
from apps.api.core.storage import storage_service

app = FastAPI(title="MESA Law API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TraceMiddleware)
app.add_exception_handler(ProblemException, problem_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(documents.router)
app.include_router(parser.router)
app.include_router(reviews.router)

# Dependency to setup Tenant Context
async def setup_tenant_context(tenant_id: str = Header("test-tenant", alias="x-tenant-id"), user: dict = Depends(get_current_user)):
    # In a real app, verify user belongs to tenant
    set_tenant_id(tenant_id)
    return tenant_id

# --- Schemas ---
class MatterCreate(BaseModel):
    title: str

class MatterResponse(BaseModel):
    id: str
    title: str
    status: str

class UploadIntentRequest(BaseModel):
    matter_id: str
    filename: str
    mime_type: str

class UploadIntentResponse(BaseModel):
    document_id: str
    revision_id: str
    presigned_url: str

class DocumentResponse(BaseModel):
    id: str
    title: str

# --- Routes ---
@app.get("/api/matters", response_model=List[MatterResponse], operation_id="listMatters")
async def list_matters(
    tenant_id: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Matter).order_by(Matter.created_at.desc()))
    matters = result.scalars().all()
    return [{"id": m.id, "title": m.title, "status": m.status} for m in matters]

@app.post("/api/matters", response_model=MatterResponse, operation_id="createMatter")
async def create_matter(
    matter_data: MatterCreate,
    tenant_id: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    matter = Matter(title=matter_data.title, tenant_id=tenant_id)
    db.add(matter)
    await db.commit()
    await db.refresh(matter)
    return {"id": matter.id, "title": matter.title, "status": matter.status}

@app.post("/api/documents/upload-intent", response_model=UploadIntentResponse, operation_id="createUploadIntent")
async def create_upload_intent(
    req: UploadIntentRequest,
    tenant_id: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    # Create Document
    doc = Document(matter_id=req.matter_id, title=req.filename, tenant_id=tenant_id)
    db.add(doc)
    await db.flush()
    
    # Create Revision
    uuid_str = str(uuid6.uuid7())
    s3_key = f"{tenant_id}/{req.matter_id}/{uuid_str}"
    
    rev = DocumentRevision(
        document_id=doc.id,
        s3_key=s3_key,
        mime_type=req.mime_type,
        scan_status="uploading"
    )
    db.add(rev)
    await db.commit()
    
    # Generate presigned URL
    url = await storage_service.generate_presigned_upload_url(s3_key, req.mime_type)
    
    return {
        "document_id": doc.id,
        "revision_id": rev.id,
        "presigned_url": url
    }

@app.get("/api/matters/{matter_id}/documents", response_model=List[DocumentResponse], operation_id="listDocuments")
async def list_documents(
    matter_id: str,
    tenant_id: str = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.matter_id == matter_id))
    docs = result.scalars().all()
    return [{"id": d.id, "title": d.title} for d in docs]
