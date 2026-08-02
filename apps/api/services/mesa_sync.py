import logging

from apps.api.core.ports.ingestion import IngestionItem, MesaIngestionPort
from apps.api.models.document import Document
from apps.api.models.parser import ParsedDocument, ParsedPage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MesaSyncService:
    def __init__(self, ingestion_port: MesaIngestionPort):
        self.ingestion = ingestion_port

    async def sync_matter(
        self, db: AsyncSession, tenant_id: str, matter_id: str
    ) -> int:
        """
        Re-syncs all parsed documents within a specific matter to MESA Core.
        """
        # Fetch all parsed documents belonging to this matter
        stmt = (
            select(ParsedDocument, Document)
            .join(Document, ParsedDocument.document_id == Document.id)
            .where(Document.matter_id == matter_id)
            .where(Document.tenant_id == tenant_id)
        )
        result = await db.execute(stmt)
        rows = result.all()

        synced_pages = 0
        for parsed_doc, doc in rows:
            synced_pages += await self.sync_document(
                db, tenant_id, parsed_doc.id, matter_id, doc.title
            )

        logger.info(
            f"Matter {matter_id} sync complete. Sent {synced_pages} pages to MESA."
        )
        return synced_pages

    async def sync_document(
        self,
        db: AsyncSession,
        tenant_id: str,
        parsed_doc_id: str,
        matter_id: str,
        doc_title: str,
    ) -> int:
        """
        Syncs all pages of a specific parsed document to MESA Core.
        """
        # Get pages
        stmt = select(ParsedPage).where(ParsedPage.parsed_document_id == parsed_doc_id)
        result = await db.execute(stmt)
        pages = result.scalars().all()

        # Get parsed document to know revision
        doc_stmt = select(ParsedDocument).where(ParsedDocument.id == parsed_doc_id)
        parsed_doc = (await db.execute(doc_stmt)).scalar_one()

        synced = 0
        for page in pages:
            item = IngestionItem(
                tenant_id=tenant_id,
                matter_id=matter_id,
                document_id=parsed_doc.document_id,
                revision_id=parsed_doc.revision_id,
                page_number=page.page_number,
                text_content=page.text_content,
                source_name=f"{doc_title} - Page {page.page_number}",
                source_type="document",
            )
            success = await self.ingestion.ingest(item)
            if success:
                synced += 1

        return synced

    async def rebuild_tenant(self, tenant_id: str) -> bool:
        """
        Calls MESA rebuild endpoint to reconstruct the FTS and Graph index for the tenant.
        """
        return await self.ingestion.rebuild_tenant(tenant_id)
