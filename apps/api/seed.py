import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

# We can use the hardcoded DEV_DATABASE_URL or from env
DATABASE_URL = os.getenv(
    "MESA_LAW_DATABASE_URL", "postgresql+psycopg://mesa:mesa@localhost:5432/mesa_law"
)


async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Insert e2e-tenant-123 into firms if it doesn't exist
        await session.execute(
            text("""
            INSERT INTO firms (id, name, created_at, updated_at, version_id) 
            VALUES ('e2e-tenant-123', 'E2E Test Firm', NOW(), NOW(), 1)
            ON CONFLICT (id) DO NOTHING;
        """)
        )
        await session.commit()
    print("Seeded firm successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
