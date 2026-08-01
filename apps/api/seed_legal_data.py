import asyncio
import logging

import uuid6
from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.core.database import AsyncSessionLocal
from apps.api.core.rls import set_tenant_id
from apps.api.models.document import Document, DocumentRevision
from apps.api.models.domain import Firm, Matter
from apps.api.models.parser import ParsedDocument, ParsedPage
from apps.api.services.mesa_sync import MesaSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_legal_data():
    tenant_id = f"legal-seed-{uuid6.uuid7()}"
    set_tenant_id(tenant_id)

    adapter = MesaV4HttpAdapter()
    sync_service = MesaSyncService(adapter)

    async with AsyncSessionLocal() as db:
        # Create Firm
        firm = Firm(id=tenant_id, name="Legal Seed Firm")
        db.add(firm)
        await db.flush()

        # 3 Anonymous Matters
        matters = []
        for i in range(3):
            matter = Matter(title=f"Anonymous Matter {i + 1}", tenant_id=tenant_id)
            db.add(matter)
            matters.append(matter)
        await db.flush()

        # Helper to create document flow
        async def create_document(matter, title, pages_texts):
            doc = Document(matter_id=matter.id, title=title, tenant_id=tenant_id)
            db.add(doc)
            await db.flush()

            rev = DocumentRevision(
                document_id=doc.id,
                s3_key=f"mock/{uuid6.uuid7()}.pdf",
                mime_type="application/pdf",
                scan_status="clean",
                tenant_id=tenant_id,
            )
            db.add(rev)
            await db.flush()

            pdoc = ParsedDocument(
                document_id=doc.id,
                revision_id=rev.id,
                parser_used="mock",
                tenant_id=tenant_id,
            )
            db.add(pdoc)
            await db.flush()

            for i, text_content in enumerate(pages_texts):
                page = ParsedPage(
                    parsed_document_id=pdoc.id,
                    page_number=i + 1,
                    text_content=text_content,
                )
                db.add(page)
            await db.flush()
            return doc

        # 2 Mevzuat & Tarihsel Sürümler (Simulated as documents in a generic matter)
        matter_mevzuat = matters[0]
        await create_document(
            matter_mevzuat,
            "6098 Türk Borçlar Kanunu",
            [
                "MADDE 1: Sözleşme, tarafların iradelerini karşılıklı ve birbirine uygun olarak açıklamalarıyla kurulur."
            ],
        )
        await create_document(
            matter_mevzuat,
            "6098 Türk Borçlar Kanunu (Eski Sürüm)",
            [
                "MADDE 1: (Mülga Metin) Akit, iki tarafın karşılıklı rızasıyla teşekkül eder."
            ],
        )
        await create_document(
            matter_mevzuat,
            "4721 Türk Medeni Kanunu",
            ["MADDE 1: Kanun, sözüyle ve özüyle değindiği bütün konularda uygulanır."],
        )
        await create_document(
            matter_mevzuat,
            "4721 Türk Medeni Kanunu (Eski Sürüm)",
            [
                "MADDE 1: (Mülga) Kanun lafzıyla ve ruhuyla temas ettiği bütün meselelerde meridir."
            ],
        )

        # 20 Yüksek Mahkeme Kararı (spread across matters 1 and 2)
        for i in range(20):
            matter_ref = matters[1] if i < 10 else matters[2]
            title = (
                f"Yargıtay {i + 1}. Hukuk Dairesi E: 2023/{i * 10} K: 2023/{i * 10 + 5}"
            )
            content = f"Dava, alacak talebine ilişkindir. Yerel mahkeme kararı incelendiğinde {i} numaralı uyuşmazlığın Borçlar Kanunu ilgili maddelerine aykırılık teşkil ettiği görülmektedir."
            await create_document(matter_ref, title, [content])

        await db.commit()

        # Rebuild/Sync MESA
        logger.info("Starting MESA sync...")
        for matter in matters:
            synced = await sync_service.sync_matter(db, tenant_id, matter.id)
            logger.info(f"Matter {matter.title} synced {synced} pages.")

    await adapter.close()
    logger.info("Golden dataset seed and sync complete.")


if __name__ == "__main__":
    asyncio.run(seed_legal_data())
