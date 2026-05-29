import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**overrides):
    base = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/app",
        "ALEMBIC_DATABASE_URL": "postgresql://user:pass@localhost:5432/app",
        "REDIS_URL": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "OPENAI_API_KEY": "sk-test",
    }
    base.update(overrides)
    return Settings(**base)


def settings_kwargs() -> dict:
    return {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite:///./backend_test.db",
        "ALEMBIC_DATABASE_URL": "sqlite+aiosqlite:///./backend_test.db",
        "JWT_SECRET_KEY": "dev-secret-change-me",
        "REDIS_URL": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "OPENAI_API_KEY": "sk-test",
    }


def test_retrieval_defaults_are_valid():
    settings = Settings(**settings_kwargs())
    assert settings.RETRIEVAL_BM25_TOP_K == 20
    assert settings.RETRIEVAL_SEMANTIC_TOP_K == 20
    assert settings.RETRIEVAL_FINAL_TOP_K == 8
    assert settings.CONTEXT_MAX_CHARS == 12_000


@pytest.mark.parametrize(
    "field",
    [
        "RETRIEVAL_BM25_TOP_K",
        "RETRIEVAL_SEMANTIC_TOP_K",
        "RETRIEVAL_FINAL_TOP_K",
        "CONTEXT_MAX_CHARS",
    ],
)
def test_retrieval_positive_values(field: str):
    kwargs = settings_kwargs()
    kwargs[field] = 0
    with pytest.raises(ValidationError):
        Settings(**kwargs)


def test_final_top_k_not_larger_than_candidate_pool():
    kwargs = settings_kwargs()
    kwargs["RETRIEVAL_BM25_TOP_K"] = 2
    kwargs["RETRIEVAL_SEMANTIC_TOP_K"] = 2
    kwargs["RETRIEVAL_FINAL_TOP_K"] = 10
    with pytest.raises(ValidationError, match="RETRIEVAL_FINAL_TOP_K"):
        Settings(**kwargs)


def test_llm_config_lazy_validation():
    kwargs = settings_kwargs()
    kwargs["LLM_API_KEY"] = None
    settings = Settings(**kwargs)
    with pytest.raises(ValueError, match="LLM_API_KEY is required"):
        settings.validate_llm_config()


def test_ingestion_settings_defaults():
    settings = _settings()
    assert settings.CHUNK_SIZE_CHARS == 1200
    assert settings.CHUNK_OVERLAP_CHARS == 200
    assert settings.EMBEDDING_MODEL == "text-embedding-3-small"
    assert settings.EMBEDDING_DIMENSION == 1536
    assert settings.EMBEDDING_BATCH_SIZE == 64
    assert settings.EMBEDDING_BASE_URL is None
    assert settings.OPENAI_API_KEY.get_secret_value() == "sk-test"


@pytest.mark.parametrize(
    "overrides",
    [
        {"CHUNK_SIZE_CHARS": 0},
        {"CHUNK_OVERLAP_CHARS": -1},
        {"CHUNK_SIZE_CHARS": 100, "CHUNK_OVERLAP_CHARS": 100},
        {"EMBEDDING_DIMENSION": 0},
        {"EMBEDDING_BATCH_SIZE": 0},
    ],
)
def test_ingestion_settings_validate_ranges(overrides):
    with pytest.raises(ValidationError):
        _settings(**overrides)


def test_embedding_base_url_empty_string_becomes_none():
    assert _settings(EMBEDDING_BASE_URL="").EMBEDDING_BASE_URL is None


def test_async_ingestion_and_celery_defaults():
    settings = _settings()
    assert settings.USE_ASYNC_INGESTION is True
    assert settings.CELERY_BROKER_URL == settings.REDIS_URL
    assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL
    assert settings.CELERY_TASK_IGNORE_RESULT is True
    assert settings.CELERY_WORKER_CONCURRENCY == 1
    assert settings.CELERY_MAX_TASKS_PER_CHILD == 50
