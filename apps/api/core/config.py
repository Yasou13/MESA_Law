from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"
    secret_key: str = "supersecret_for_development"
    api_port: int = 8001
    postgres_user: str = "mesa"
    postgres_password: str = "mesa"
    postgres_db: str = "mesa_law"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    mesa_backend_url: str = "http://localhost:8000"
    mesa_api_key: str = "dev-api-key"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
