from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "local"
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str
    JWT_SECRET_KEY: str = DEFAULT_DEV_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8080"
    REDIS_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION_NAME: str = "documents"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    STORAGE_ROOT: str = "backend/storage"
    MAX_UPLOAD_BYTES: int = Field(default=52_428_800, ge=1, le=200 * 1024 * 1024)

    @field_validator("ENVIRONMENT")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.strip().lower()

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @computed_field
    @property
    def storage_root_path(self) -> Path:
        return Path(self.STORAGE_ROOT).expanduser().resolve()

    @model_validator(mode="after")
    def validate_secret(self) -> "Settings":
        if self.ENVIRONMENT not in {"local", "development", "test"} and (
            not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == DEFAULT_DEV_SECRET
        ):
            raise ValueError("JWT_SECRET_KEY must be set to a non-default value outside local/test")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
