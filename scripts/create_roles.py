import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def create_roles():
    url = "postgresql+psycopg://mesa:mesa@127.0.0.1:5432/mesa_law"
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        for role, pwd, extra in [
            ("mesa_law_app", "app_pass", "NOSUPERUSER NOBYPASSRLS"),
            ("mesa_law_worker", "worker_pass", "NOSUPERUSER NOBYPASSRLS"),
            ("mesa_law_migrator", "migrator_pass", "SUPERUSER")
        ]:
            try:
                await conn.execute(text(f"CREATE ROLE {role} WITH LOGIN PASSWORD '{pwd}' {extra};"))
            except Exception:
                await conn.execute(text(f"ALTER ROLE {role} WITH LOGIN PASSWORD '{pwd}' {extra};"))
            
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mesa_law_app;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mesa_law_app;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mesa_law_worker;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mesa_law_worker;"))
        print("Roles and permissions created successfully.")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_roles())
