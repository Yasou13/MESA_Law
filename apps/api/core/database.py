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

import os

if os.getenv("MESA_LAW_ENVIRONMENT", "development") != "test":
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    SQLAlchemyInstrumentor().instrument(
        engine=async_engine.sync_engine,
        enable_commenter=True,
        commenter_options={}
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
