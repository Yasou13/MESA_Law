from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Async engine and session for FastAPI endpoints
async_engine = create_async_engine(
    settings.effective_database_url,
    pool_pre_ping=True,
    echo=settings.env == "development",
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

# Sync engine and session for Alembic / background jobs
engine = create_engine(
    settings.effective_database_url,
    pool_pre_ping=True,
    echo=settings.env == "development",
)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=Session)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
