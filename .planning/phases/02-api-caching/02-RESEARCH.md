# Phase 2: API & Caching - Research

**Researched:** 2026-02-08
**Domain:** FastAPI routing/DI, Redis caching, cache stampede prevention, API integration testing
**Confidence:** HIGH (official docs verified, existing codebase analyzed, patterns cross-referenced)

## Summary

This phase delivers three FastAPI endpoints (`/api/v2/halls`, `/api/v2/menus`, `/api/v2/open-now`) backed by Redis caching with 30-minute TTL and PostgreSQL fallback. The existing codebase from Phase 1 provides SQLModel models (`DiningHall`, `Menu`), async database infrastructure (`db.py` with `async_session_factory`), three working parsers (Sodexo, BAMCO, Pomona), and a fallback orchestrator (`get_menu_with_fallback`). Phase 2 builds on top of this foundation by adding the FastAPI application scaffold, API routers, a Redis caching layer, and cache stampede prevention.

The most significant design decision is the caching architecture. The PRD specifies "fetch on demand, cache the result" (no scheduled jobs). When a menu request arrives, the API checks Redis first. On cache miss, it runs the parser via `get_menu_with_fallback`, caches the result, and returns it. Cache stampede prevention is critical because multiple clients requesting the same hall/date/meal simultaneously during a cache miss would all trigger parser runs. The recommended approach combines in-process request coalescing (asyncio-native, no external library needed) with TTL jitter (randomize TTL between 25-35 minutes instead of a fixed 30) to avoid synchronized cache expirations.

The `/open-now` endpoint requires a `DiningHours` model that does not yet exist in the database. The PRD defines `dining_hours` and `dining_hours_overrides` tables, which need SQLModel implementations. Hours evaluation requires timezone-aware datetime comparison in Pacific time (the existing `config.py` already has `timezone: str = "America/Los_Angeles"`). Seed data for all 7 halls' operating hours will be needed.

**Primary recommendation:** Use FastAPI's `lifespan` context manager to initialize Redis and DB connections, `APIRouter` for endpoint organization, `Depends()` for per-request session/redis injection, in-process asyncio-based request coalescing for stampede prevention, and `fakeredis` for integration tests.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.115 | HTTP framework | Already in project stack; async, Pydantic-native |
| redis[hiredis] | >=5.0 | Async Redis client | Official redis-py with async support; hiredis for 10x parse speed |
| uvicorn | latest | ASGI server | Standard FastAPI production server |
| httpx | >=0.28.1 | Already installed | Used by parsers; also used for async integration tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fakeredis[json] | latest | Redis mock for testing | Integration tests without a real Redis server |
| asgi-lifespan | latest | Lifespan trigger in tests | Required for async tests that depend on app lifespan events |
| anyio | latest | Async test backend | Already used by FastAPI; compatible with `pytest.mark.anyio` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| redis-py async | aioredis | aioredis is now merged into redis-py; use redis-py directly |
| fakeredis | pytest-mock-resources | PMR requires Docker/real Redis; fakeredis is pure-Python, faster |
| In-process coalescing | singleflight PyPI package | External dep unnecessary; 20 lines of asyncio code achieves same result |
| TTL jitter | Probabilistic early expiration (XFetch) | XFetch is more complex; jitter is simpler and sufficient for this scale |

**Installation:**
```bash
pip install "fastapi[standard]" "redis[hiredis]" uvicorn "fakeredis[json]" asgi-lifespan
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, CORS, mount routers
│   ├── config.py             # Settings (existing, add redis_url)
│   ├── db.py                 # Async DB engine/session (existing)
│   ├── redis.py              # Async Redis client lifecycle
│   ├── dependencies.py       # Shared Depends() providers (session, redis)
│   ├── models/
│   │   ├── __init__.py       # (existing)
│   │   ├── enums.py          # (existing)
│   │   ├── dining_hall.py    # (existing)
│   │   ├── menu.py           # (existing)
│   │   └── dining_hours.py   # NEW: DiningHours + DiningHoursOverride
│   ├── parsers/              # (existing, unchanged)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── halls.py          # GET /api/v2/halls
│   │   ├── menus.py          # GET /api/v2/menus
│   │   └── open_now.py       # GET /api/v2/open-now
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── halls.py          # Response models for halls endpoint
│   │   ├── menus.py          # Response models for menus endpoint
│   │   └── open_now.py       # Response models for open-now endpoint
│   └── services/
│       ├── __init__.py
│       ├── cache.py          # Redis cache get/set with TTL jitter
│       ├── coalesce.py       # In-process request coalescing
│       ├── menu_service.py   # Menu fetch orchestration (cache -> parser -> fallback)
│       └── hours_service.py  # Hours lookup + open-now evaluation
├── tests/
│   ├── conftest.py           # (existing, extend with app/redis fixtures)
│   ├── test_api_halls.py     # Integration tests for /halls
│   ├── test_api_menus.py     # Integration tests for /menus
│   └── test_api_open_now.py  # Integration tests for /open-now
├── alembic/                  # (existing)
├── pyproject.toml            # (existing, add new deps)
└── requirements.txt          # (existing, add new deps)
```

### Pattern 1: FastAPI Lifespan for Resource Management
**What:** Initialize Redis and DB connections in an async context manager that runs at app startup/shutdown.
**When to use:** Always -- this is the modern FastAPI pattern (replaces deprecated `@app.on_event`).
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create Redis connection pool
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    yield
    # Shutdown: close Redis
    await app.state.redis.aclose()

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: Dependency Injection for Per-Request Resources
**What:** Use `Depends()` to inject database sessions and Redis clients into route handlers.
**When to use:** Every route handler that needs DB or Redis access.
**Example:**
```python
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.db import get_session

async def get_redis(request: Request) -> Redis:
    return request.app.state.redis

@router.get("/api/v2/halls")
async def list_halls(
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
):
    ...
```

### Pattern 3: Cache-Aside with Fallback Chain
**What:** Check Redis cache first, on miss run parser, persist to DB, cache result.
**When to use:** Every menu data request.
**Example:**
```python
async def get_menu(hall_id: str, date: str, meal: str, session, redis_client):
    # 1. Check Redis cache
    cache_key = f"menu:{hall_id}:{date}:{meal}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. Cache miss: run parser with fallback
    parser = get_parser(hall_id)
    menu, is_stale, fetched_at = await get_menu_with_fallback(
        parser, hall_id, target_date, session
    )

    # 3. Cache the result (with jitter)
    if menu:
        ttl = 1800 + random.randint(-300, 300)  # 25-35 min
        await redis_client.setex(cache_key, ttl, menu.model_dump_json())

    return menu
```

### Pattern 4: In-Process Request Coalescing
**What:** Deduplicate concurrent requests for the same cache key using asyncio.Event.
**When to use:** Prevents cache stampede when multiple clients request the same uncached menu simultaneously.
**Example:**
```python
import asyncio

_inflight: dict[str, asyncio.Future] = {}

async def coalesced_fetch(key: str, fetch_fn):
    if key in _inflight:
        return await _inflight[key]

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    _inflight[key] = future

    try:
        result = await fetch_fn()
        future.set_result(result)
        return result
    except Exception as exc:
        future.set_exception(exc)
        raise
    finally:
        _inflight.pop(key, None)
```

### Pattern 5: Response Models (Pydantic v2)
**What:** Separate Pydantic models for API responses (not SQLModel table models).
**When to use:** Every endpoint -- ensures consistent serialization and OpenAPI docs.
**Example:**
```python
from pydantic import BaseModel

class HallResponse(BaseModel):
    id: str
    name: str
    college: str
    color: str | None = None

class MenuItemResponse(BaseModel):
    name: str
    tags: list[str] = []

class StationResponse(BaseModel):
    name: str
    items: list[MenuItemResponse]

class MenuResponse(BaseModel):
    hall_id: str
    date: str
    meal: str
    stations: list[StationResponse]
    is_stale: bool = False
    fetched_at: str | None = None
```

### Anti-Patterns to Avoid
- **Module-level Redis client:** Do NOT create a Redis connection at import time. Use lifespan to initialize and `app.state` to store. Module-level connections cause "attached to different loop" errors in testing.
- **No response models:** Do NOT return raw SQLModel objects from endpoints. Always define separate Pydantic response schemas to control serialization and prevent leaking internal fields.
- **Fixed TTL on all keys:** Do NOT use the same exact TTL for all cached menus. This causes synchronized expirations and cache stampedes. Always add jitter.
- **Nested Depends for heavy ops:** Do NOT put parser invocation inside a `Depends()`. Parsers are slow I/O -- they belong in service functions called from the route handler, not in the dependency chain.
- **Blocking Redis calls:** Do NOT use `redis.Redis` (sync). Always use `redis.asyncio.Redis` to avoid blocking the event loop.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Redis client/pool | Custom connection manager | `redis.asyncio.from_url()` | Handles pooling, reconnection, timeouts automatically |
| ASGI test setup | Manual app instantiation | `httpx.AsyncClient` + `ASGITransport` | Official FastAPI testing pattern, handles ASGI protocol correctly |
| Lifespan in tests | Skip lifespan or mock it | `asgi-lifespan.LifespanManager` | Ensures Redis/DB init runs in test, identical to production |
| Redis mocking | `unittest.mock.MagicMock` | `fakeredis.FakeAsyncRedis` | Implements actual Redis commands; MagicMock silently passes invalid ops |
| JSON in Redis | Manual `json.dumps`/`json.loads` | Pydantic `.model_dump_json()` / `.model_validate_json()` | Type-safe, handles dates/enums, validates on deserialization |

**Key insight:** The Redis caching layer is deceptively simple but has many edge cases (connection drops, serialization errors, TTL race conditions). Using `redis-py`'s built-in async client with `fakeredis` for tests avoids hand-rolling error-prone connection management and mock implementations.

## Common Pitfalls

### Pitfall 1: Event Loop Mismatch in Tests
**What goes wrong:** Tests fail with "RuntimeError: Task attached to a different event loop" or "Future attached to a different loop."
**Why it happens:** Creating Redis/DB connections at module level or in sync fixtures, then trying to use them in async test functions that run on a different event loop.
**How to avoid:** Create all async resources (Redis, DB sessions) inside async fixtures or inside the lifespan context manager. Use `fakeredis.FakeAsyncRedis()` inside async fixtures, not at module scope.
**Warning signs:** Tests pass individually but fail when run together; tests pass locally but fail in CI.

### Pitfall 2: asyncio_mode Conflict
**What goes wrong:** Tests marked with `@pytest.mark.asyncio` conflict with AnyIO plugin, causing collection errors.
**Why it happens:** The project already has `asyncio_mode = "auto"` in `pyproject.toml`. When both pytest-asyncio and AnyIO are installed, auto mode conflicts.
**How to avoid:** Stick with `asyncio_mode = "auto"` and `@pytest.mark.asyncio` (already used by Phase 1 tests). Do NOT mix `@pytest.mark.anyio` markers. If FastAPI installs AnyIO, configure `[tool.pytest.ini_options]` to avoid conflicts.
**Warning signs:** `PytestCollectionWarning` or `PytestUnhandledCoroutineWarning` during test collection.

### Pitfall 3: Cache Key Collisions
**What goes wrong:** Different menus overwrite each other in cache, or stale data is served for wrong hall/date/meal.
**Why it happens:** Cache keys don't include all discriminating dimensions, or date format is inconsistent.
**How to avoid:** Use a strict cache key format: `menu:{hall_id}:{YYYY-MM-DD}:{meal}`. Always normalize date to ISO format before key construction. Never include timestamps or request-specific data in cache keys.
**Warning signs:** API returns lunch menu when dinner was requested; menus from yesterday appear for today.

### Pitfall 4: Timezone Confusion in open-now
**What goes wrong:** `/open-now` reports halls as closed during operating hours, or open when they are closed.
**Why it happens:** Comparing naive UTC datetime with Pacific time dining hours, or using `datetime.now()` (naive local time) instead of timezone-aware time.
**How to avoid:** Always use `datetime.now(ZoneInfo("America/Los_Angeles"))` for current Pacific time. Store dining hours as naive `time` objects (they're always in Pacific time). Compare `current_time.time()` against `start_time` and `end_time` from `dining_hours` table.
**Warning signs:** Open/closed status changes at wrong times; daylight saving transitions cause 1-hour errors.

### Pitfall 5: Missing Dining Hours Data
**What goes wrong:** `/open-now` returns empty list because `dining_hours` table has no rows.
**Why it happens:** The `dining_hours` table needs seed data for all 7 halls x all meals x all days. Without it, no hall can ever be "open."
**How to avoid:** Create an Alembic data migration or seed script that populates default dining hours. Include this as a required step in Phase 2 implementation.
**Warning signs:** `/open-now` always returns `[]`; `/halls` works but shows no hours.

### Pitfall 6: Coalescing Memory Leak
**What goes wrong:** The in-flight request map grows unbounded, leaking memory.
**Why it happens:** If a `fetch_fn` raises an exception and the `finally` block doesn't clean up, the key stays in `_inflight` forever. Or if the future is never resolved.
**How to avoid:** Always clean up in a `finally` block. Add a timeout to prevent indefinite waits. Consider using `asyncio.wait_for()` with a reasonable timeout (e.g., 30 seconds) on the future.
**Warning signs:** Memory usage grows over time; log shows "waiting for in-flight request" that never resolves.

## Code Examples

Verified patterns from official sources:

### FastAPI Application Entry Point
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
# Source: https://fastapi.tiangolo.com/tutorial/cors/
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import halls, menus, open_now

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    yield
    await app.state.redis.aclose()

app = FastAPI(
    title="5C Menu API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(halls.router, prefix="/api/v2")
app.include_router(menus.router, prefix="/api/v2")
app.include_router(open_now.router, prefix="/api/v2")
```

### Redis Cache Service
```python
# Source: https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
import json
import random
from redis.asyncio import Redis

BASE_TTL = 1800  # 30 minutes
JITTER_RANGE = 300  # +/- 5 minutes

async def cache_get(redis_client: Redis, key: str) -> dict | None:
    raw = await redis_client.get(key)
    if raw is None:
        return None
    return json.loads(raw)

async def cache_set(redis_client: Redis, key: str, data: dict) -> None:
    ttl = BASE_TTL + random.randint(-JITTER_RANGE, JITTER_RANGE)
    await redis_client.setex(key, ttl, json.dumps(data))

def menu_cache_key(hall_id: str, date_str: str, meal: str) -> str:
    return f"menu:{hall_id}:{date_str}:{meal}"
```

### DiningHours SQLModel
```python
import datetime as _dt
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint

class DiningHours(SQLModel, table=True):
    __tablename__ = "dining_hours"
    __table_args__ = (
        UniqueConstraint("hall_id", "day_of_week", "meal", name="uq_hours_hall_day_meal"),
    )

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    day_of_week: int  # 0=Sunday, 6=Saturday
    meal: str = Field(max_length=20)
    start_time: _dt.time
    end_time: _dt.time
    is_active: bool = Field(default=True)

class DiningHoursOverride(SQLModel, table=True):
    __tablename__ = "dining_hours_overrides"
    __table_args__ = (
        UniqueConstraint("hall_id", "date", "meal", name="uq_override_hall_date_meal"),
    )

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    date: _dt.date
    meal: str | None = Field(default=None, max_length=20)
    start_time: _dt.time | None = None
    end_time: _dt.time | None = None
    reason: str | None = Field(default=None, max_length=200)
```

### Open-Now Service Logic
```python
import datetime as _dt
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dining_hours import DiningHours, DiningHoursOverride

async def get_open_halls(session: AsyncSession, tz_name: str) -> list[dict]:
    now = _dt.datetime.now(ZoneInfo(tz_name))
    current_time = now.time()
    current_dow = now.isoweekday() % 7  # 0=Sunday convention

    # Check for overrides first (date-specific closures/changes)
    override_stmt = select(DiningHoursOverride).where(
        DiningHoursOverride.date == now.date()
    )
    override_result = await session.execute(override_stmt)
    overrides = {
        (o.hall_id, o.meal): o
        for o in override_result.scalars().all()
    }

    # Get regular hours for today's day_of_week
    hours_stmt = select(DiningHours).where(
        DiningHours.day_of_week == current_dow,
        DiningHours.is_active == True,
    )
    hours_result = await session.execute(hours_stmt)
    all_hours = hours_result.scalars().all()

    open_halls = set()
    for hours in all_hours:
        override = overrides.get((hours.hall_id, hours.meal))
        if override:
            if override.start_time is None:  # Closed override
                continue
            start, end = override.start_time, override.end_time
        else:
            start, end = hours.start_time, hours.end_time

        if start <= current_time <= end:
            open_halls.add(hours.hall_id)

    return list(open_halls)
```

### Integration Test Setup
```python
# Source: https://fastapi.tiangolo.com/advanced/async-tests/
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.dependencies import get_redis
from fakeredis import FakeAsyncRedis

@pytest.fixture
async def fake_redis():
    r = FakeAsyncRedis(decode_responses=True)
    yield r
    await r.aclose()

@pytest.fixture
async def client(fake_redis):
    # Override Redis dependency
    app.dependency_overrides[get_redis] = lambda: fake_redis

    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_list_halls(client):
    response = await client.get("/api/v2/halls")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    assert all("id" in h for h in data)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.93+ (2023) | `on_event` is deprecated; use `lifespan` exclusively |
| `aioredis` separate package | `redis.asyncio` (built into redis-py) | redis-py 4.2+ (2022) | aioredis merged into redis-py; install `redis` not `aioredis` |
| `TestClient` (sync) | `AsyncClient` + `ASGITransport` | httpx 0.23+ (2022) | Required for testing async endpoints properly |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 deprecation | Already adopted in Phase 1 codebase |
| `pytz` timezone library | `zoneinfo` (stdlib) | Python 3.9+ | No external dependency needed for timezone handling |

**Deprecated/outdated:**
- `aioredis`: Merged into redis-py. Do not install separately.
- `@app.on_event`: Use `lifespan` parameter instead. If `lifespan` is set, `on_event` handlers are silently ignored.
- `TestClient` for async routes: Use `httpx.AsyncClient` with `ASGITransport`.

## Open Questions

1. **Dining hours seed data**
   - What we know: PRD lists 7 halls with typical meal periods. The `dining_hours` table schema is defined.
   - What's unclear: Exact start/end times for each hall/meal/day. College websites are the source but hours change each semester.
   - Recommendation: Create seed data with reasonable defaults based on typical dining hall hours (breakfast 7:30-10, lunch 11-13:30, dinner 17-20). These can be updated via the admin panel in Phase 4. Include seed data in an Alembic migration or fixture file.

2. **Lifespan + fakeredis interaction in tests**
   - What we know: `LifespanManager` triggers the app's lifespan which creates a real Redis client on `app.state.redis`. Tests need to override this with `fakeredis`.
   - What's unclear: Whether dependency override alone is sufficient, or if the lifespan's Redis client creation needs to be conditioned on environment.
   - Recommendation: Use FastAPI's `dependency_overrides` to inject `FakeAsyncRedis` into route handlers. The lifespan-created client will exist but won't be used if dependencies are overridden. Alternatively, accept a Redis URL from settings and point it at fakeredis in test config. Validate during implementation.

3. **Parser registry for hall_id -> parser mapping**
   - What we know: Three parser classes exist (SodexoParser, BonAppetitParser, PomonaParser). Each hall maps to one parser type. The `DiningHall` model has `vendor_type` field.
   - What's unclear: How to map hall_id to the correct parser instance at runtime.
   - Recommendation: Create a simple registry dict in `services/menu_service.py` that maps `vendor_type` to parser class, and instantiate with hall-specific config. The `DiningHall.vendor_type` field already exists for this lookup.

4. **Response envelope format**
   - What we know: The codebase conventions doc suggests `{"success": true, "data": {...}, "error": null}` envelope.
   - What's unclear: Whether to use envelope wrapping or return data directly (more RESTful, better OpenAPI docs).
   - Recommendation: Return data directly from endpoints (list of halls, menu object, etc.). FastAPI's response model system works best with direct returns. Add error handling via `HTTPException` for error cases. Envelopes add complexity without value for this API.

## Sources

### Primary (HIGH confidence)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) - Lifespan context manager pattern, deprecated on_event
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) - AsyncClient + ASGITransport, LifespanManager requirement
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/) - CORSMiddleware configuration
- [redis-py Async Examples](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html) - Async Redis client, connection pool, aclose()
- [redis-py Connections](https://redis.readthedocs.io/en/stable/connections.html) - from_url(), pool config, decode_responses
- [Python zoneinfo docs](https://docs.python.org/3/library/zoneinfo.html) - ZoneInfo for America/Los_Angeles
- [fakeredis docs](https://fakeredis.readthedocs.io/) - FakeAsyncRedis, JSON module support

### Secondary (MEDIUM confidence)
- [Cache Stampede Prevention - OneUptime](https://oneuptime.com/blog/post/2026-01-30-cache-stampede-prevention/view) - Layered defense: coalescing + jitter + locking
- [singleflight on GitHub](https://github.com/aarondwi/singleflight) - Python singleflight with async support (validates in-process pattern)
- [request-coalescing-py on GitHub](https://github.com/hexolan/request-coalescing-py) - Asyncio request coalescing for FastAPI (validates approach)
- [FastAPI + Redis Lifespan Gist](https://gist.github.com/nicksonthc/525742d9a81d3950b443810e8899ee0e) - Redis class pattern with lifespan

### Tertiary (LOW confidence)
- None -- all findings verified against primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs for FastAPI, redis-py, fakeredis all verified
- Architecture: HIGH - Patterns derived from official FastAPI docs and verified community practices
- Pitfalls: HIGH - Event loop issues, cache key design, timezone handling are well-documented problems
- Cache stampede: MEDIUM - In-process coalescing pattern validated via two GitHub implementations but custom code needed (no established library for Python asyncio)

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (stable domain -- FastAPI and redis-py are mature)
