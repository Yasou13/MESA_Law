import asyncio
import os

from sqlalchemy import String, bindparam, text
from sqlalchemy.ext.asyncio import create_async_engine


async def create_roles():
    url = os.environ["MESA_LAW_MIGRATOR_DATABASE_URL"]
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        for role, password, extra in [
            (
                "mesa_law_app",
                os.environ["MESA_LAW_APP_DB_PASSWORD"],
                "NOSUPERUSER NOBYPASSRLS",
            ),
            (
                "mesa_law_worker",
                os.environ["MESA_LAW_WORKER_DB_PASSWORD"],
                "NOSUPERUSER NOBYPASSRLS",
            ),
            (
                "mesa_law_migrator",
                os.environ["MESA_LAW_MIGRATOR_DB_PASSWORD"],
                "SUPERUSER",
            ),
        ]:
            exists = await conn.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)"),
                {"role": role},
            )
            verb = "ALTER" if exists else "CREATE"
            statement = text(
                f"{verb} ROLE {role} WITH LOGIN PASSWORD :password {extra}"
            ).bindparams(
                bindparam("password", type_=String(), literal_execute=True)
            )
            await conn.execute(
                statement,
                {"password": password},
            )

        await conn.execute(
            text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mesa_law_app")
        )
        await conn.execute(
            text(
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mesa_law_app"
            )
        )
        await conn.execute(
            text(
                "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mesa_law_worker"
            )
        )
        await conn.execute(
            text(
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public "
                "TO mesa_law_worker"
            )
        )
        print("Roles and permissions created successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_roles())
