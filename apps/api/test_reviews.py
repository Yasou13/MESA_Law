import pytest
from apps.api.core.database import AsyncSessionLocal
from apps.api.models.review import ReviewItem
from sqlalchemy import select


@pytest.mark.asyncio
async def test_review_item_model_exists():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ReviewItem).limit(1))
        item = result.scalars().first()
        # Ensure we can query the table without errors
        assert item is None or isinstance(item, ReviewItem)

