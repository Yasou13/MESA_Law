"""Real PostgreSQL RLS checks against the configured isolated test database."""

import uuid

import pytest
from apps.api.core.config import settings
from apps.api.models.domain import Firm, Matter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_tenant_rls_isolation() -> None:
    engine = create_async_engine(settings.effective_database_url, echo=False)
    admin_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    try:
        async with admin_session() as session:
            session.add_all(
                [
                    Firm(id=tenant_a, name="Firm A"),
                    Firm(id=tenant_b, name="Firm B"),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    Matter(title="Matter A", tenant_id=tenant_a),
                    Matter(title="Matter B", tenant_id=tenant_b),
                ]
            )
            await session.commit()

        async with engine.begin() as connection:
            await connection.execute(text("SET ROLE mesa_law_app"))
            await connection.execute(
                text("SELECT set_config('app.current_tenant', :tenant, true)"),
                {"tenant": tenant_a},
            )
            rows_a = (
                await connection.execute(
                    text("SELECT title, tenant_id FROM matters ORDER BY title")
                )
            ).all()
            assert [(row.title, row.tenant_id) for row in rows_a] == [
                ("Matter A", tenant_a)
            ]

            await connection.execute(
                text("SELECT set_config('app.current_tenant', :tenant, true)"),
                {"tenant": tenant_b},
            )
            rows_b = (
                await connection.execute(
                    text("SELECT title, tenant_id FROM matters ORDER BY title")
                )
            ).all()
            assert [(row.title, row.tenant_id) for row in rows_b] == [
                ("Matter B", tenant_b)
            ]
            await connection.execute(text("RESET ROLE"))
    finally:
        async with engine.begin() as connection:
            await connection.execute(
                text("DELETE FROM matters WHERE tenant_id IN (:tenant_a, :tenant_b)"),
                {"tenant_a": tenant_a, "tenant_b": tenant_b},
            )
            await connection.execute(
                text("DELETE FROM firms WHERE id IN (:tenant_a, :tenant_b)"),
                {"tenant_a": tenant_a, "tenant_b": tenant_b},
            )
        await engine.dispose()
