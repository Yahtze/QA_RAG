import redis.asyncio as redis

from app.core.config import Settings


async def ping_redis(settings: Settings) -> None:
    client = redis.from_url(settings.REDIS_URL)
    try:
        await client.ping()
    finally:
        await client.aclose()
