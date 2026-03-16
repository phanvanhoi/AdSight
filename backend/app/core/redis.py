import redis.asyncio as aioredis

from app.config import settings


class RedisClient:
    def __init__(self):
        self._redis = None

    async def initialize(self):
        self._redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    @property
    def client(self):
        if self._redis is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._redis

    async def close(self):
        if self._redis:
            await self._redis.close()


redis_client = RedisClient()


async def get_redis():
    try:
        return redis_client.client
    except RuntimeError:
        return None
