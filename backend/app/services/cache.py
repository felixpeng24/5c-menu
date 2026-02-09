"""Redis cache layer for menu data.

Provides get/set operations with jittered TTL to prevent synchronized
cache expiration (thundering herd). Base TTL is 30 minutes with +/- 5
minutes of random jitter, yielding an effective range of 25-35 minutes.
"""

import json
import random

from redis.asyncio import Redis

BASE_TTL: int = 1800  # 30 minutes in seconds
JITTER_RANGE: int = 300  # +/- 5 minutes in seconds


def menu_cache_key(hall_id: str, date_str: str, meal: str) -> str:
    """Build a Redis cache key for a specific menu query."""
    return f"menu:{hall_id}:{date_str}:{meal}"


async def cache_get(redis_client: Redis, key: str) -> dict | None:
    """Retrieve a cached menu dict from Redis.

    Returns the deserialized dict if the key exists, otherwise None.
    """
    raw = await redis_client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(redis_client: Redis, key: str, data: dict) -> None:
    """Store a menu dict in Redis with a jittered TTL.

    TTL is randomized within [BASE_TTL - JITTER_RANGE, BASE_TTL + JITTER_RANGE]
    (i.e., 25-35 minutes) to prevent synchronized expiration across keys.
    """
    ttl = BASE_TTL + random.randint(-JITTER_RANGE, JITTER_RANGE)
    await redis_client.setex(key, ttl, json.dumps(data))
