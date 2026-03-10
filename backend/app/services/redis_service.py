import json

import redis.asyncio as aioredis
import structlog

from app.core.redis import get_redis

logger = structlog.get_logger()


class RedisService:
    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

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
        client = await self._get_client()
        raw_client = aioredis.from_url(
            str(client.connection_pool.connection_kwargs.get("url", "")),
            decode_responses=False,
        )
        await raw_client.setex(f"snapshot:{camera_id}", ttl, jpeg_bytes)
        await raw_client.close()

    async def get_snapshot(self, camera_id: str) -> bytes | None:
        client = await self._get_client()
        raw_client = aioredis.from_url(
            str(client.connection_pool.connection_kwargs.get("url", "")),
            decode_responses=False,
        )
        data = await raw_client.get(f"snapshot:{camera_id}")
        await raw_client.close()
        return data


redis_service = RedisService()
