import json

import redis.asyncio as aioredis
import structlog

from app.config import settings
from app.core.redis import get_redis

logger = structlog.get_logger()


class RedisService:
    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._redis_binary: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def _get_binary_client(self) -> aioredis.Redis:
        if self._redis_binary is None:
            self._redis_binary = aioredis.from_url(
                settings.redis_url,
                decode_responses=False,
            )
        return self._redis_binary

    async def publish(self, channel: str, message: dict) -> None:
        client = await self._get_client()
        await client.publish(channel, json.dumps(message, default=str))

    async def subscribe(self, *channels: str):
        client = await self._get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def set_cached(self, key: str, value: dict, ttl: int = 60) -> None:
        client = await self._get_client()
        await client.setex(key, ttl, json.dumps(value, default=str))

    async def get_cached(self, key: str) -> dict | None:
        client = await self._get_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_snapshot(self, camera_id: str, jpeg_bytes: bytes, ttl: int = 10) -> None:
        client = await self._get_binary_client()
        await client.setex(f"snapshot:{camera_id}", ttl, jpeg_bytes)

    async def get_snapshot(self, camera_id: str) -> bytes | None:
        client = await self._get_binary_client()
        return await client.get(f"snapshot:{camera_id}")


redis_service = RedisService()
