"""Optional Redis cache layer.

All functions are no-ops when Redis is not connected (REDIS_URL not set).
Errors from an already-connected Redis (e.g. network blip) are caught
internally and logged at DEBUG level — callers always get a safe default.
"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_redis = None  # redis.asyncio.Redis instance, or None


async def connect(url: str) -> None:
    """Connect to Redis and verify with PING. Raises on failure."""
    import redis.asyncio as aioredis  # imported lazily — not required if Redis disabled

    global _redis
    client = aioredis.from_url(url, decode_responses=True)
    await client.ping()
    _redis = client


async def get(key: str) -> Any | None:
    """Return deserialised value for *key*, or None if absent / Redis unavailable."""
    if not _redis:
        return None
    try:
        raw = await _redis.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("Redis get(%s) failed: %s", key, exc)
        return None


async def set(key: str, value: Any, ttl: int | None = None) -> None:
    """Serialise *value* to JSON and store under *key* with optional TTL (seconds)."""
    if not _redis:
        return
    try:
        await _redis.set(key, json.dumps(value), ex=ttl)
    except Exception as exc:
        logger.debug("Redis set(%s) failed: %s", key, exc)


async def hgetall(key: str) -> dict[str, str]:
    """Return all field-value pairs in hash *key*, or {} if absent / unavailable."""
    if not _redis:
        return {}
    try:
        return await _redis.hgetall(key) or {}
    except Exception as exc:
        logger.debug("Redis hgetall(%s) failed: %s", key, exc)
        return {}


async def hset(key: str, field: str, value: str) -> None:
    """Set *field* → *value* in hash *key*."""
    if not _redis:
        return
    try:
        await _redis.hset(key, field, value)
    except Exception as exc:
        logger.debug("Redis hset(%s, %s) failed: %s", key, field, exc)
