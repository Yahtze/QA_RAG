import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_parses_cors_and_defaults(tmp_path):
    s = Settings(
        ENVIRONMENT="local",
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/app",
        ALEMBIC_DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/app",
        JWT_SECRET_KEY="dev-secret-change-me",
        REDIS_URL="redis://localhost:6379/0",
        QDRANT_URL="http://localhost:6333",
        STORAGE_ROOT=str(tmp_path),
        BACKEND_CORS_ORIGINS="http://localhost:5173,http://localhost:8080",
    )
    assert s.cors_origins == ["http://localhost:5173", "http://localhost:8080"]
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30


def test_non_local_rejects_default_jwt_secret(tmp_path):
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/app",
            ALEMBIC_DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/app",
            JWT_SECRET_KEY="dev-secret-change-me",
            REDIS_URL="redis://localhost:6379/0",
            QDRANT_URL="http://localhost:6333",
            STORAGE_ROOT=str(tmp_path),
        )
