from collections.abc import AsyncGenerator

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session as _get_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (re-exported from app.db)."""
    async for session in _get_session():
        yield session


def get_redis(request: Request) -> Redis:
    """Return the Redis client stored on app.state by lifespan."""
    return request.app.state.redis
