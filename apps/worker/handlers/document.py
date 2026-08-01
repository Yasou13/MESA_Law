import asyncio
import contextlib
import hashlib
import logging
import os
import struct

from apps.api.core.storage import storage_service
from apps.api.core.utils import utc_now
from apps.api.models.document import Document, DocumentRevision, DocumentState
from apps.api.models.queue import Job
from apps.worker.jobs import RetryableJobError, TerminalJobError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.document")

CLAMAV_HOST = os.getenv("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", "3310"))
SCAN_CHUNK_BYTES = 1024 * 1024


async def scan_with_clamav(data: bytes) -> bool:
    """Scan the exact byte sequence that will become the immutable object."""
    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(CLAMAV_HOST, CLAMAV_PORT), timeout=10
        )
        writer.write(b"zINSTREAM\0")
        for start in range(0, len(data), SCAN_CHUNK_BYTES):
            chunk = data[start : start + SCAN_CHUNK_BYTES]
            writer.write(struct.pack("!I", len(chunk)))
            writer.write(chunk)
            await writer.drain()
        writer.write(struct.pack("!I", 0))
        await writer.drain()
        response = (
            (await asyncio.wait_for(reader.read(4096), timeout=60))
            .decode(errors="replace")
            .strip()
        )
        logger.info("ClamAV completed a document scan")
        if "FOUND" in response:
            return False
        if "OK" in response:
            return True
        raise RetryableJobError("ClamAV returned an unrecognized response")
    except (TimeoutError, ConnectionError, OSError) as exc:
        raise RetryableJobError(f"ClamAV unavailable: {exc}") from exc
    finally:
        if writer is not None:
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()


async def handle_scan_document(payload: dict, session: AsyncSession) -> None:
    revision_id = payload.get("revision_id")
    quarantine_key = payload.get("s3_key")
    document_id = payload.get("document_id")
    expected_sha256 = payload.get("expected_sha256")
    expected_size = payload.get("expected_size")
    mime_type = payload.get("mime_type")
    if not all(
        [
            revision_id,
            quarantine_key,
            document_id,
            expected_sha256,
            expected_size,
            mime_type,
        ]
    ):
        raise TerminalJobError("Missing immutable scan payload fields")

    revision = await session.get(DocumentRevision, revision_id)
    document = await session.get(Document, document_id)
    if revision is None or document is None or revision.document_id != document.id:
        raise TerminalJobError("Document revision not found for scanning")
    if revision.is_canonical:
        if revision.file_hash == expected_sha256 and revision.s3_key:
            return
        raise TerminalJobError("Canonical revision cannot be overwritten")
    if revision.quarantine_key != quarantine_key:
        raise TerminalJobError("Quarantine object key does not match the revision")

    file_bytes = await storage_service.get_object_bytes(
        quarantine_key, max_bytes=100 * 1024 * 1024 + 1
    )
    if file_bytes is None:
        raise TerminalJobError("Quarantine object not found")
    actual_sha256 = hashlib.sha256(file_bytes).hexdigest()
    if len(file_bytes) != expected_size or actual_sha256 != expected_sha256:
        raise TerminalJobError(
            "Quarantine bytes changed after validation; refusing canonical promotion"
        )
    if revision.file_hash != actual_sha256 or revision.mime_type != mime_type:
        raise TerminalJobError("Revision metadata does not match validated bytes")

    if not await scan_with_clamav(file_bytes):
        revision.scan_status = DocumentState.INFECTED
        revision.failure_reason = "Malware scanner reported infected content"
        revision.is_canonical = False
        return

    extensions = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }
    try:
        extension = extensions[mime_type]
    except KeyError as exc:
        raise TerminalJobError(f"Unsupported MIME type: {mime_type}") from exc
    immutable_key = (
        f"immutable/{document.tenant_id}/{document.matter_id}/{document.id}/"
        f"{revision.id}/{actual_sha256}{extension}"
    )
    await storage_service.promote_quarantine_object(
        quarantine_key,
        immutable_key,
        validated_body=file_bytes,
        sha256=actual_sha256,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
    )

    revision.s3_key = immutable_key
    revision.is_canonical = True
    revision.immutable_at = utc_now()
    revision.scan_status = DocumentState.CLEAN
    revision.failure_reason = None
    session.add(
        Job(
            type="PARSE_DOCUMENT",
            tenant_id=document.tenant_id,
            matter_id=document.matter_id,
            idempotency_key=f"parse:{revision.id}:{actual_sha256}",
            payload={
                "document_id": document.id,
                "revision_id": revision.id,
                "s3_key": immutable_key,
                "matter_id": document.matter_id,
            },
        )
    )
    logger.info("Promoted clean revision %s to immutable storage", revision.id)
