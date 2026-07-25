import asyncio
import logging
import struct
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.document import DocumentRevision
from apps.api.models.queue import Job
from apps.api.core.storage import storage_service

logger = logging.getLogger("worker.document")

CLAMAV_HOST = os.getenv("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", "3310"))

async def scan_with_clamav(stream) -> bool:
    """Returns True if clean, False if infected."""
    try:
        reader, writer = await asyncio.open_connection(CLAMAV_HOST, CLAMAV_PORT)
        writer.write(b'zINSTREAM\0')
        
        async for chunk in stream:
            if chunk:
                # Send length
                writer.write(struct.pack('!I', len(chunk)))
                # Send chunk
                writer.write(chunk)
                await writer.drain()
        
        # EOF
        writer.write(struct.pack('!I', 0))
        await writer.drain()
        
        response = await reader.read(4096)
        writer.close()
        await writer.wait_closed()
        
        response_text = response.decode().strip()
        logger.info(f"ClamAV response: {response_text}")
        
        if "OK" in response_text and "FOUND" not in response_text:
            return True
        return False
    except Exception as e:
        logger.error(f"Error scanning with ClamAV: {e}")
        # If we can't scan, assume unsafe or retry. We'll raise exception so job retries.
        raise

async def handle_scan_document(payload: dict, session: AsyncSession):
    revision_id = payload.get("revision_id")
    s3_key = payload.get("s3_key")
    
    if not revision_id or not s3_key:
        logger.error("Missing revision_id or s3_key in payload")
        return
        
    logger.info(f"Scanning document revision {revision_id} at {s3_key}")
    
    # Download stream from S3
    async with storage_service.session.client('s3', endpoint_url=storage_service.endpoint_url,
                                     aws_access_key_id=storage_service.aws_access_key_id,
                                     aws_secret_access_key=storage_service.aws_secret_access_key,
                                     config=storage_service.config) as s3:
        try:
            response = await s3.get_object(Bucket=storage_service.bucket_name, Key=s3_key)
            stream = response['Body']
            
            is_clean = await scan_with_clamav(stream)
            
            rev = await session.get(DocumentRevision, revision_id)
            if rev:
                rev.scan_status = "clean" if is_clean else "infected"
                
                if is_clean:
                    # Queue the parsing job
                    job = Job(
                        type="PARSE_DOCUMENT",
                        payload={"document_id": document_id, "revision_id": revision_id, "s3_key": s3_key}
                    )
                    session.add(job)
                    logger.info(f"Queued PARSE_DOCUMENT for revision {revision_id}")
                    
                await session.commit()
                logger.info(f"Revision {revision_id} marked as {rev.scan_status}")
            else:
                logger.error(f"Revision {revision_id} not found in DB")
                
        except Exception as e:
            logger.error(f"Failed to process document scan: {e}")
            raise
