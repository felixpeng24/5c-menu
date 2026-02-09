import redis.asyncio as aioredis


def create_redis(url: str) -> aioredis.Redis:
    """Create an async Redis client from a URL.

    The caller (lifespan in main.py) is responsible for storing this
    on app.state and closing it on shutdown.
    """
    return aioredis.from_url(url, decode_responses=True)
