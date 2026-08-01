"""Write one-run random Compose credentials to the GitHub Actions env file."""

import os
import secrets
from pathlib import Path


def main() -> int:
    destination = os.getenv("GITHUB_ENV")
    if os.getenv("CI") != "true" or not destination:
        print("Refusing to emit credentials outside GitHub Actions CI")
        return 1

    values = {
        "POSTGRES_PASSWORD": secrets.token_urlsafe(48),
        "MESA_LAW_APP_DB_PASSWORD": secrets.token_urlsafe(48),
        "MESA_LAW_WORKER_DB_PASSWORD": secrets.token_urlsafe(48),
        "MESA_LAW_MIGRATOR_DB_PASSWORD": secrets.token_urlsafe(48),
        "MESA_LAW_SECRET_KEY": secrets.token_urlsafe(48),
        "MINIO_ROOT_USER": "mesa-ci",
        "MINIO_ROOT_PASSWORD": secrets.token_urlsafe(48),
        "KEYCLOAK_ADMIN": "mesa-ci-admin",
        "KEYCLOAK_ADMIN_PASSWORD": secrets.token_urlsafe(48),
        "KEYCLOAK_CLIENT_SECRET": secrets.token_urlsafe(48),
        "NEXTAUTH_SECRET": secrets.token_urlsafe(48),
        "GRAFANA_ADMIN_PASSWORD": secrets.token_urlsafe(48),
        "MESA_LAW_ENVIRONMENT": "test",
        "MESA_LAW_TEST_AUTH_ENABLED": "true",
        "MESA_LAW_INTELLIGENCE_ADAPTER": "mock",
    }
    with Path(destination).open("a", encoding="utf-8") as env_file:
        env_file.writelines(f"{key}={value}\n" for key, value in values.items())
    print("Wrote ephemeral CI credentials to the protected GitHub Actions env file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
