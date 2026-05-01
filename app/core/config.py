from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "FlowCred API"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Se definido (ex.: sqlite:////app/data/db.local), tem prioridade sobre Postgres.
    DATABASE_URL: str | None = Field(default=None)

    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""

    BACKEND_CORS_ORIGINS: str = ""

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    INITIAL_ADMIN_USERNAME: str | None = None
    INITIAL_ADMIN_PASSWORD: str | None = None

    # 1 / true / yes: após migrations/admin, cria cliente + proposta demo (idempotente).
    SEED_DEV_DATA: bool = False

    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            return self.DATABASE_URL.strip()
        if (
            self.POSTGRES_SERVER.strip()
            and self.POSTGRES_DB.strip()
            and self.POSTGRES_USER.strip()
        ):
            return (
                f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return "sqlite:///./db.local"

    @property
    def is_sqlite(self) -> bool:
        return self.SQLALCHEMY_DATABASE_URI.startswith("sqlite")

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        if not self.BACKEND_CORS_ORIGINS.strip():
            return []
        return [item.strip() for item in self.BACKEND_CORS_ORIGINS.split(",") if item.strip()]


settings = Settings()
