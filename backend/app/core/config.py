from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator
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
    OPENAI_API_KEY: SecretStr | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = Field(default=1536, ge=1)
    EMBEDDING_BATCH_SIZE: int = Field(default=64, ge=1)
    CHUNK_SIZE_CHARS: int = Field(default=1200, ge=1)
    CHUNK_OVERLAP_CHARS: int = Field(default=200, ge=0)
    STORAGE_ROOT: str = "backend/storage"
    MAX_UPLOAD_BYTES: int = Field(default=52_428_800, ge=1, le=200 * 1024 * 1024)
    USE_ASYNC_INGESTION: bool = True
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_TASK_IGNORE_RESULT: bool = True
    CELERY_WORKER_CONCURRENCY: int = Field(default=1, ge=1)
    CELERY_MAX_TASKS_PER_CHILD: int = Field(default=50, ge=1)
    RETRIEVAL_BM25_TOP_K: int = Field(default=20, ge=1)
    RETRIEVAL_SEMANTIC_TOP_K: int = Field(default=20, ge=1)
    RETRIEVAL_FINAL_TOP_K: int = Field(default=8, ge=1)
    CONTEXT_MAX_CHARS: int = Field(default=12_000, ge=1)
    LLM_BASE_URL: str | None = None
    LLM_API_KEY: SecretStr | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    SEMANTIC_CACHE_ENABLED: bool = False
    SEMANTIC_CACHE_TTL_SECONDS: int = Field(default=86_400, ge=1)
    SEMANTIC_CACHE_MIN_SIMILARITY: float = Field(default=0.85, ge=0.0, le=1.0)
    SEMANTIC_CACHE_TIMEOUT_MS: int = Field(default=75, ge=1)
    SEMANTIC_CACHE_INDEX_NAME: str = "idx:semcache"
    SEMANTIC_CACHE_KEY_PREFIX: str = "semcache:"

    @field_validator("ENVIRONMENT")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("EMBEDDING_BASE_URL", mode="before")
    @classmethod
    def normalize_embedding_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("LLM_BASE_URL", mode="before")
    @classmethod
    def normalize_llm_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @computed_field
    @property
    def storage_root_path(self) -> Path:
        root = Path(self.STORAGE_ROOT).expanduser()
        if root.is_absolute():
            return root.resolve()
        project_root = Path(__file__).resolve().parents[3]
        return (project_root / root).resolve()

    @computed_field
    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @computed_field
    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @model_validator(mode="after")
    def validate_secret(self) -> "Settings":
        if self.ENVIRONMENT not in {"local", "development", "test"} and (
            not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == DEFAULT_DEV_SECRET
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be set to a non-default value outside local/test"
            )
        if self.CHUNK_OVERLAP_CHARS >= self.CHUNK_SIZE_CHARS:
            raise ValueError("CHUNK_OVERLAP_CHARS must be less than CHUNK_SIZE_CHARS")
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        if (
            self.RETRIEVAL_FINAL_TOP_K
            > self.RETRIEVAL_BM25_TOP_K + self.RETRIEVAL_SEMANTIC_TOP_K
        ):
            raise ValueError(
                "RETRIEVAL_FINAL_TOP_K cannot exceed retrieval candidate pool"
            )
        return self

    def validate_llm_config(self) -> None:
        if self.LLM_API_KEY is None:
            raise ValueError("LLM_API_KEY is required")
        if not self.LLM_MODEL.strip():
            raise ValueError("LLM_MODEL is required")


@lru_cache
def get_settings() -> Settings:
    return Settings()
