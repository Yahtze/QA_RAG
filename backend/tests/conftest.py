import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./backend_test.db")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "sqlite+aiosqlite:///./backend_test.db")
os.environ.setdefault("JWT_SECRET_KEY", "dev-secret-change-me")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("STORAGE_ROOT", "backend/storage_test")

from app.api.deps import get_db_session, get_settings_dep  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        ENVIRONMENT="test",
        DATABASE_URL="sqlite+aiosqlite:///./backend_test.db",
        ALEMBIC_DATABASE_URL="sqlite+aiosqlite:///./backend_test.db",
        JWT_SECRET_KEY="dev-secret-change-me",
        REDIS_URL="redis://localhost:6379/0",
        QDRANT_URL="http://localhost:6333",
        STORAGE_ROOT=str(tmp_path / "storage"),
    )


@pytest_asyncio.fixture
async def db_session(settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(
    db_session: AsyncSession, settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    def _get_settings() -> Settings:
        return settings

    app.dependency_overrides[get_db_session] = _get_db
    app.dependency_overrides[get_settings_dep] = _get_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient) -> dict[str, str]:
    r = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password12345", "name": "User"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
