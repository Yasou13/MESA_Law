import asyncio

import pytest
from apps.api.core.database import AsyncSessionLocal
from apps.api.models.review import AuditLog, ReviewQueue
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_reviews():
    # 1. Insert a mock AI-generated review item
    async with AsyncSessionLocal() as db:
        item = ReviewQueue(
            tenant_id="e2e-tenant-123",
            matter_id="mock-matter-id",
            entity_type="claim",
            entity_id="claim-1",
            proposed_content={"claim": "Haksiz fesih"},
            status="pending"
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        item_id = item.id
        print(f"Created pending review item: {item_id}")

    # 2. Test API GET
    async with AsyncClient(base_url="http://localhost:8001", headers={"x-tenant-id": "e2e-tenant-123"}) as client:
        res = await client.get("/reviews")
        print(f"GET /reviews: {res.status_code}")
        
        # 3. Test API POST approve
        res = await client.post(f"/reviews/{item_id}/approve")
        print(f"POST approve: {res.status_code}, {res.json()}")

    # 4. Verify DB Audit log and Status
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ReviewQueue).where(ReviewQueue.id == item_id))
        item = res.scalar_one()
        print(f"Status after approve: {item.status}")
        print(f"External use ready at: {item.external_use_ready_at}")

        res = await db.execute(select(AuditLog).where(AuditLog.entity_id == "claim-1"))
        audit = res.scalars().all()
        print(f"Audit log entries: {len(audit)}")
        for a in audit:
            print(f"- Action: {a.action}, Details: {a.details}")

if __name__ == "__main__":
    asyncio.run(test_reviews())
