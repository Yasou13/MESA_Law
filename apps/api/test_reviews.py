import asyncio

import pytest
from apps.api.core.database import AsyncSessionLocal
from apps.api.models.review import AuditLog, ReviewQueue
from httpx import AsyncClient
from sqlalchemy import select


from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models.review import AuditLog, ReviewItem
import uuid6

@pytest.mark.asyncio
            print(f"- Action: {a.action}, Details: {a.details}")

if __name__ == "__main__":
    asyncio.run(test_reviews())
