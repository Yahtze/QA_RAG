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
