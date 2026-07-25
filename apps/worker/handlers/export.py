import logging
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models.draft import Draft
from apps.api.core.storage import storage_service

logger = logging.getLogger("worker.export")

async def handle_export_draft(payload: dict, session: AsyncSession):
    draft_id = payload.get("draft_id")
    fmt = payload.get("format", "pdf").lower()
    
    if not draft_id:
        logger.error("Missing draft_id in EXPORT_DRAFT payload")
        return
        
    draft = await session.get(Draft, draft_id)
    if not draft:
        logger.error(f"Draft {draft_id} not found for export")
        return
        
    logger.info(f"Exporting draft {draft_id} (version {draft.version}) as {fmt}")
    
    # Simple export conversion representation
    content_bytes = f"--- MESA Law Draft Export ({fmt.upper()}) ---\nTitle: {draft.title}\nVersion: {draft.version}\n\n{draft.content}".encode('utf-8')
    content_type = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    s3_key = f"{draft.tenant_id}/{draft.matter_id}/exports/draft_{draft.id}_v{draft.version}.{fmt}"
    
    try:
        async with storage_service.session.client('s3', endpoint_url=storage_service.endpoint_url,
                                         aws_access_key_id=storage_service.aws_access_key_id,
                                         aws_secret_access_key=storage_service.aws_secret_access_key,
                                         config=storage_service.config) as s3:
            await s3.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key,
                Body=content_bytes,
                ContentType=content_type
            )
        logger.info(f"Successfully exported draft {draft_id} to S3 key {s3_key}")
    except Exception as e:
        logger.error(f"Failed to export draft {draft_id} to S3: {e}", exc_info=True)
        raise
