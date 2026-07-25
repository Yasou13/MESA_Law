from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    secret_key: str = "MUST_BE_PROVIDED_IN_ENV"
    api_port: int = 8001
    postgres_user: str = "mesa"
    postgres_password: str = "mesa"
    postgres_db: str = "mesa_law"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # If set via MESA_LAW_DATABASE_URL env var, this takes priority
    database_url: str | None = None
    
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    mesa_backend_url: str = "http://localhost:8000"
    mesa_api_key: str = ""
    
    model_config = SettingsConfigDict(env_prefix="MESA_LAW_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def effective_database_url(self) -> str:
        """Returns DATABASE_URL from env if set, otherwise constructs from components."""
        if self.database_url:
            return self.database_url
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
