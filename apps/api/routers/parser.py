from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.ratelimit import limiter
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.parser import ParsedDocument, ParsedPage

router = APIRouter()

class ParsedDocumentResponse(BaseModel):
    id: str
    document_id: str
    revision_id: str
    parsing_revision: int
    parser_used: str
    status: str

class ParsedPageResponse(BaseModel):
    id: str
    page_number: int
    text_content: str
    layout_data: dict | None = None

@router.get("/document/{document_id}", response_model=list[ParsedDocumentResponse], operation_id="listParsedDocuments")
@limiter.limit("60/minute")
async def list_parsed_documents(
    request: Request,
    document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParsedDocument).where(
            ParsedDocument.document_id == document_id,
            ParsedDocument.tenant_id == context.tenant_id
        ).order_by(ParsedDocument.parsing_revision.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "document_id": d.document_id,
            "revision_id": d.revision_id,
            "parsing_revision": d.parsing_revision,
            "parser_used": d.parser_used,
            "status": d.status
        }
        for d in docs
    ]

@router.get("/{parsed_document_id}/pages", response_model=list[ParsedPageResponse], operation_id="listParsedPages")
@limiter.limit("60/minute")
async def list_parsed_pages(
    request: Request,
    parsed_document_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    pdoc = await db.get(ParsedDocument, parsed_document_id)
    if not pdoc or pdoc.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="Parsed document not found")
        
    result = await db.execute(
        select(ParsedPage).where(
            ParsedPage.parsed_document_id == parsed_document_id
        ).order_by(ParsedPage.page_number.asc())
    )
    pages = result.scalars().all()
    return [
        {
            "id": p.id,
            "page_number": p.page_number,
            "text_content": p.text_content,
            "layout_data": p.layout_data
        }
        for p in pages
    ]

