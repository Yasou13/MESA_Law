from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings

# Async engine and session for FastAPI endpoints
async_engine = create_async_engine(
    settings.database_url.replace("postgresql+psycopg://", "postgresql+psycopg_async://"),
    pool_pre_ping=True,
    echo=settings.env == "development",
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

# Sync engine and session for Alembic / background jobs
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.env == "development",
)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=Session)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
