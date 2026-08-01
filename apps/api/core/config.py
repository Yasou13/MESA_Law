from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = Field(
        default="development",
        validation_alias=AliasChoices(
            "MESA_LAW_ENVIRONMENT", "MESA_LAW_ENV", "ENVIRONMENT", "ENV", "env"
        ),
    )
    secret_key: str = "MUST_BE_PROVIDED_IN_ENV"
    api_port: int = 8001
    postgres_user: str = "mesa"
    postgres_password: str = "mesa"
    postgres_db: str = "mesa_law"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # If set via MESA_LAW_DATABASE_URL env var, this takes priority
    database_url: str | None = None

    algorithm: str = "RS256"
    access_token_expire_minutes: int = 30
    mesa_backend_url: str = "http://localhost:8000"
    mesa_api_key: str = ""
    intelligence_adapter: str = Field(
        default="mesa_v4",
        validation_alias=AliasChoices(
            "MESA_LAW_INTELLIGENCE_ADAPTER", "INTELLIGENCE_ADAPTER"
        ),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "MESA_LAW_REDIS_URL"),
    )
    test_auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "MESA_LAW_TEST_AUTH_ENABLED", "TEST_AUTH_ENABLED"
        ),
    )
    mesa_rebuild_enabled: bool = False
    external_research_enabled: bool = False
    drafting_ai_enabled: bool = False
    deadline_ai_enabled: bool = False
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    keycloak_client_id: str = Field(
        default="mesa-client",
        validation_alias=AliasChoices(
            "KEYCLOAK_CLIENT_ID", "MESA_LAW_KEYCLOAK_CLIENT_ID"
        ),
    )
    keycloak_client_secret: str = Field(
        default="mesa-client-secret",
        validation_alias=AliasChoices(
            "KEYCLOAK_CLIENT_SECRET", "MESA_LAW_KEYCLOAK_CLIENT_SECRET"
        ),
    )
    keycloak_issuer: str = Field(
        default="http://localhost:8080/realms/mesa_law",
        validation_alias=AliasChoices(
            "KEYCLOAK_PUBLIC_ISSUER", "KEYCLOAK_ISSUER", "MESA_LAW_KEYCLOAK_ISSUER"
        ),
    )
    keycloak_jwks_url: str = Field(
        default="http://localhost:8080/realms/mesa_law/protocol/openid-connect/certs",
        validation_alias=AliasChoices(
            "KEYCLOAK_JWKS_URL", "MESA_LAW_KEYCLOAK_JWKS_URL"
        ),
    )
    keycloak_internal_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "KEYCLOAK_INTERNAL_URL", "MESA_LAW_KEYCLOAK_INTERNAL_URL"
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="MESA_LAW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_database_url(self) -> str:
        """Returns DATABASE_URL from env if set, otherwise constructs from components."""
        if self.database_url:
            return self.database_url
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def is_secure_environment(self) -> bool:
        """Returns True if the environment is considered secure (production, staging, pilot)."""
        return self.env.lower() in ("production", "staging", "pilot")


settings = Settings()


def validate_production_settings():
    if settings.is_secure_environment:
        insecure_defaults = [
            "MUST_BE_PROVIDED_IN_ENV",
            "password123",
            "supersecret_dev_key",
            "mesa-client-secret",
            "supersecret_nextauth_key_for_dev_only",
        ]
        if (
            settings.secret_key in insecure_defaults
            or settings.keycloak_client_secret in insecure_defaults
        ):
            raise RuntimeError(
                f"CRITICAL SECURITY ERROR: Secure environment '{settings.env}' detected with insecure default secrets. Startup aborted."
            )
        if not settings.keycloak_issuer.startswith(
            "https://"
        ) or not settings.keycloak_jwks_url.startswith("https://"):
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: Secure environments require HTTPS Keycloak issuer and JWKS URLs."
            )
        if not settings.cors_origins or any(
            origin == "*" or not origin.startswith("https://")
            for origin in settings.cors_origins
        ):
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: Secure environments require an explicit HTTPS CORS allowlist."
            )
        if settings.intelligence_adapter != "mesa_v4" or not settings.mesa_api_key:
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: Secure environments require the MESA v4 adapter and API key."
            )

    if settings.test_auth_enabled and settings.env != "test":
        raise RuntimeError(
            f"CRITICAL SECURITY ERROR: MESA_LAW_TEST_AUTH_ENABLED is set to true but environment is '{settings.env}'. Test auth can only be enabled in 'test' environment. Startup aborted."
        )


validate_production_settings()
