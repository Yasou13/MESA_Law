import asyncio
import logging
import os
import tempfile

from apps.api.core.config import settings
from apps.api.core.storage import storage_service
from apps.api.models.document import Document, DocumentState
from apps.api.models.parser import ParsedDocument, ParsedPage
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from llama_parse import LlamaParse
    HAS_LLAMA_PARSE = True
except ImportError:
    HAS_LLAMA_PARSE = False

try:
    import importlib.util
    HAS_FITZ = importlib.util.find_spec("fitz") is not None
except ImportError:
    HAS_FITZ = False
    
try:
    import docx2txt
    HAS_DOCX2TXT = True
except ImportError:
    HAS_DOCX2TXT = False

logger = logging.getLogger("worker.parser")

async def handle_parse_document(payload: dict, session: AsyncSession):
    document_id = payload.get("document_id")
    revision_id = payload.get("revision_id")
    s3_key = payload.get("s3_key")
    
    if not document_id or not revision_id or not s3_key:
        logger.error("Missing required payload fields")
        return
        
    # Get the document to get the tenant_id
    doc = await session.get(Document, document_id)
    if not doc:
        logger.error(f"Document {document_id} not found")
        return
        
    tenant_id = doc.tenant_id
        
    logger.info(f"Parsing document {document_id} (revision {revision_id})")
    
    # Download file to temp preserving extension
    ext = os.path.splitext(s3_key)[1].lower() if s3_key else ".pdf"
    if not ext:
        ext = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_path = temp_file.name
        
    try:
        async with storage_service.session.client('s3', endpoint_url=storage_service.endpoint_url,
                                         aws_access_key_id=storage_service.aws_access_key_id,
                                         aws_secret_access_key=storage_service.aws_secret_access_key,
                                         config=storage_service.config) as s3:
            await s3.download_file(storage_service.bucket_name, s3_key, temp_path)
            
            # Parse
            parsed_text = ""
            pages = []
            
            api_key = os.getenv("LLAMA_CLOUD_API_KEY")
            
            is_docx = (ext == ".docx")
            parser_used_name = "mock"
            
            if HAS_LLAMA_PARSE and api_key and not is_docx:
                logger.info("Using LlamaParse for document extraction")
                parser = LlamaParse(api_key=api_key, result_type="markdown")
                documents = await asyncio.to_thread(parser.load_data, temp_path)
                parser_used_name = "llama-parse"
                
                for i, d in enumerate(documents):
                    pages.append({"page_number": i + 1, "text": d.text, "layout": None})
                    parsed_text += f"\n\n--- Page {i+1} ---\n\n" + d.text
            elif is_docx and HAS_DOCX2TXT:
                logger.info("Using docx2txt for docx extraction")
                text = await asyncio.to_thread(docx2txt.process, temp_path)
                parser_used_name = "docx2txt"
                pages = [{"page_number": 1, "text": text, "layout": None}]
                parsed_text = text
            elif HAS_FITZ and not is_docx:
                logger.info("Using PyMuPDF (fitz) for PDF extraction")
                parser_used_name = "pymupdf-fitz"
                
                from apps.worker.parsers.pdf import PyMuPDFParser
                with open(temp_path, "rb") as f:
                    pdf_bytes = f.read()
                    
                pdf_parser = PyMuPDFParser()
                pages_data = []
                async for p_data in pdf_parser.parse(pdf_bytes):
                    pages_data.append(p_data)
                
                pages = []
                for pd in pages_data:
                    pages.append({
                        "page_number": pd["page_number"],
                        "text": pd["text_content"],
                        "layout": pd["layout_data"]
                    })
                    parsed_text += f"\n\n--- Page {pd['page_number']} ---\n\n" + pd["text_content"]
            else:
                if settings.is_secure_environment:
                    raise RuntimeError("No parser available. Mock extraction is strictly prohibited in production.")
                logger.warning("No parser available. Using mock extraction.")
                parser_used_name = "mock"
                pages = [
                    {"page_number": 1, "text": "Mock parsed content for page 1.", "layout": None}
                ]
                parsed_text = "Mock parsed content for page 1."
                
            parsed_doc = ParsedDocument(
                tenant_id=tenant_id,
                document_id=document_id,
                revision_id=revision_id,
                parser_used=parser_used_name,
                status="completed"
            )
            session.add(parsed_doc)
            
            # Update Revision Status
            from apps.api.models.document import DocumentRevision
            rev = await session.get(DocumentRevision, revision_id)
            if rev:
                rev.scan_status = DocumentState.READY
                
            await session.flush()
            
            # Phase 7: Mark old citations as STALE_REVISION
            from sqlalchemy import text
            await session.execute(
                text("UPDATE draft_citations SET verification_state = 'STALE_REVISION' WHERE document_id = :doc_id AND document_revision_id != :new_rev AND verification_state != 'STALE_REVISION'"),
                {"doc_id": document_id, "new_rev": revision_id}
            )
            
            # Save pages and chunks
            from apps.api.models.parser import DocumentChunk
            
            for page in pages:
                p = ParsedPage(
                    parsed_document_id=parsed_doc.id,
                    page_number=page["page_number"],
                    text_content=page["text"],
                    layout_data=page.get("layout")
                )
                session.add(p)
                await session.flush()
                
                layout_data = page.get("layout") or {}
                blocks = layout_data.get("blocks", [])
                
                for chunk_idx, block in enumerate(blocks):
                    bbox = block.get("bbox")
                    block_text = block.get("text", "")
                    if not block_text.strip():
                        continue
                        
                    bbox_id = block.get("id", f"b{chunk_idx}")
                    watermark = f"[MESA_WATERMARK: {document_id}:{p.id}:{bbox_id}]"
                    watermarked_text = f"{block_text}\n{watermark}"
                    
                    chunk = DocumentChunk(
                        tenant_id=tenant_id,
                        document_id=document_id,
                        page_id=p.id,
                        chunk_index=chunk_idx,
                        chunk_type="block",
                        text_content=block_text,
                        watermarked_text=watermarked_text,
                        bbox=bbox
                    )
                    session.add(chunk)
                
            from apps.api.models.queue import Job
            
            # Upload parsed markdown to S3
            parsed_s3_key = f"{tenant_id}/{doc.matter_id}/parsed_{revision_id}.md"
            await s3.put_object(
                Bucket=storage_service.bucket_name,
                Key=parsed_s3_key,
                Body=parsed_text.encode('utf-8'),
                ContentType="text/markdown"
            )
            logger.info(f"Uploaded parsed document to {parsed_s3_key}")
            
            # Trigger extraction job
            job = Job(
                type="EXTRACT_LEGAL_DATA",
                tenant_id=payload["tenant_id"],
                payload={
                    "parsed_document_id": parsed_doc.id,
                    "matter_id": doc.matter_id
                }
            )
            session.add(job)
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Failed to parse document: {e}", exc_info=True)
        raise
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
