"""In-process request coalescing for cache-miss stampede prevention.

When multiple concurrent requests miss the cache for the same key,
only one parser invocation runs. All other waiters receive the same
result via a shared asyncio.Future.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

_inflight: dict[str, asyncio.Future] = {}

_FETCH_TIMEOUT: float = 30.0  # seconds


async def coalesced_fetch(key: str, fetch_fn: Callable[[], Awaitable[T]]) -> T:
    """Execute fetch_fn once per key, coalescing concurrent callers.

    If another coroutine is already fetching for the same key, this
    coroutine awaits the in-flight future instead of running fetch_fn
    again. Includes a 30-second timeout to prevent indefinite hangs.

    Args:
        key: Unique identifier for deduplication (typically the cache key).
        fetch_fn: Async callable that produces the result.

    Returns:
        The result of fetch_fn (shared across all concurrent callers).

    Raises:
        Whatever fetch_fn raises (propagated to all waiters).
        asyncio.TimeoutError: If fetch_fn exceeds the timeout.
    """
    if key in _inflight:
        return await _inflight[key]

    loop = asyncio.get_running_loop()
    future: asyncio.Future[T] = loop.create_future()
    _inflight[key] = future

    try:
        result = await asyncio.wait_for(fetch_fn(), timeout=_FETCH_TIMEOUT)
        future.set_result(result)
        return result
    except Exception as exc:
        future.set_exception(exc)
        raise
    finally:
        _inflight.pop(key, None)
