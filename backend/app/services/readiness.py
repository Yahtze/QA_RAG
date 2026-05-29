from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings
from app.services.qdrant_collection import QdrantCollectionService
from app.services.redis import ping_redis


@dataclass
class ReadinessReport:
    postgres: str
    redis: str
    qdrant: str


class ReadinessService:
    def __init__(self, engine: AsyncEngine, settings: Settings):
        self.engine = engine
        self.settings = settings

    async def check(self) -> ReadinessReport:
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        redis = "skipped"
        if self.settings.USE_ASYNC_INGESTION:
            await ping_redis(self.settings)
            redis = "ok"
        await QdrantCollectionService(self.settings).ensure_collection()
        return ReadinessReport(postgres="ok", redis=redis, qdrant="ok")
