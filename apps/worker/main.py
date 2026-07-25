import asyncio
import logging
import signal
import sys
from sqlalchemy.ext.asyncio import AsyncSession

from apps.worker.core.queue import Worker
from apps.worker.handlers.document import handle_scan_document
from apps.worker.handlers.parser import handle_parse_document
from apps.worker.handlers.extraction import handle_extract_legal_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("worker")

async def dummy_handler(payload: dict, session: AsyncSession):
    logger.info(f"Dummy handler processing: {payload}")

async def main():
    logger.info("Starting MESA Law Worker...")
    worker = Worker(batch_size=10, lease_minutes=5)
    
    # Register handlers
    handlers = [
        "SCAN_DOCUMENT",
        "PARSE_DOCUMENT", 
        "OCR_DOCUMENT",
        "EXTRACT_LEGAL_FACTS",
        "BUILD_LEXICAL_INDEX",
        "SYNC_MESA_DOCUMENT",
        "PUBLISH_OUTBOX",
        "EXPORT_DRAFT"
    ]
    for h in handlers:
        if h == "SCAN_DOCUMENT":
            worker.register(h, handle_scan_document)
        elif h == "PARSE_DOCUMENT":
            worker.register(h, handle_parse_document)
        elif h == "EXTRACT_LEGAL_DATA":
            worker.register(h, handle_extract_legal_data)
        else:
            worker.register(h, dummy_handler)

    loop = asyncio.get_running_loop()
    
    def handle_sigterm():
        logger.info("Received stop signal, shutting down gracefully...")
        worker.stop()
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_sigterm)

    logger.info("Worker started, waiting for jobs...")
    try:
        await worker.start()
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
    finally:
        logger.info("Worker stopped.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
