import asyncio
import logging
import signal

from apps.api.core.observability import setup_observability
from apps.worker.core.queue import Worker
from apps.worker.handlers.document import handle_scan_document
from apps.worker.handlers.export import handle_export_draft
from apps.worker.handlers.extraction import handle_extract_legal_data
from apps.worker.handlers.ocr import handle_ocr_document
from apps.worker.handlers.parser import handle_parse_document
from apps.worker.handlers.sync import (
    handle_build_lexical_index,
    handle_publish_review,
    handle_sync_mesa_document,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("worker")


async def main() -> None:
    setup_observability(service_name="mesa-law-worker")
    logger.info("Starting MESA Law Worker...")
    import os

    concurrency = int(os.getenv("MESA_LAW_WORKER_CONCURRENCY", "1"))
    if concurrency < 1 or concurrency > 4:
        raise RuntimeError("MESA_LAW_WORKER_CONCURRENCY must be between 1 and 4")
    worker = Worker(batch_size=concurrency, lease_minutes=5)
    logger.info(f"Worker concurrency set to {concurrency}")

    # Register real handlers for all supported pipeline jobs
    worker.register("SCAN_DOCUMENT", handle_scan_document)
    worker.register("PARSE_DOCUMENT", handle_parse_document)
    worker.register("OCR_DOCUMENT", handle_ocr_document)
    worker.register("EXTRACT_LEGAL_FACTS", handle_extract_legal_data)
    worker.register("EXTRACT_LEGAL_DATA", handle_extract_legal_data)
    worker.register("BUILD_LEXICAL_INDEX", handle_build_lexical_index)
    worker.register("SYNC_MESA_DOCUMENT", handle_sync_mesa_document)
    worker.register("EXPORT_DRAFT", handle_export_draft)
    worker.register("PUBLISH_REVIEW", handle_publish_review)

    loop = asyncio.get_running_loop()

    def handle_sigterm() -> None:
        logger.info("Received stop signal, shutting down gracefully...")
        worker.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_sigterm)

    logger.info("Worker started, waiting for jobs...")
    try:
        await worker.start()
    except Exception:
        logger.exception("Worker crashed")
        raise
    finally:
        logger.info("Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
