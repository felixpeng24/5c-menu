# Architecture Research

**Domain:** College dining menu aggregation app (multi-vendor scraper + real-time crowding)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  Next.js Web │  │  Expo Mobile │  │  Admin Panel │                      │
│  │  (Vercel)    │  │  (iOS/Andr.) │  │  (Next.js)   │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                  │                              │
├─────────┴─────────────────┴──────────────────┴──────────────────────────────┤
│                         HTTPS / REST API                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                           API LAYER (FastAPI on Railway)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │  Halls   │  │  Menus   │  │ Crowding │  │  Admin   │                    │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │                    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                    │
│       │              │             │              │                          │
│  ┌────┴──────────────┴─────────────┴──────────────┴─────┐                   │
│  │                 SERVICE LAYER                         │                   │
│  │  HallService  MenuService  CrowdingService  AuthSvc  │                   │
│  └────┬──────────────┬─────────────┬──────────────┬─────┘                   │
│       │              │             │              │                          │
├───────┴──────────────┴─────────────┴──────────────┴─────────────────────────┤
│                           DATA LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  PostgreSQL  │  │    Redis     │  │   Parsers    │                      │
│  │  (persist)   │  │  (cache/rt)  │  │  (scrapers)  │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                       EXTERNAL DATA SOURCES                                 │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐                              │
│  │  Sodexo  │  │ Bon Appetit  │  │  Pomona  │                              │
│  │  Website  │  │   Website    │  │  Website │                              │
│  └──────────┘  └──────────────┘  └──────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Next.js Web** | Responsive menu browsing, hall list, date navigation, dark mode | Next.js 14 App Router + Tailwind CSS + React Query. Client-side rendering; React Query fetches from API. |
| **Expo Mobile** | Native mobile menu browsing + location pings for crowding | Expo Router + React Query + expo-location. Generates session IDs, sends foreground location pings. |
| **Admin Panel** | Hours editing, override management, parser status dashboard | Next.js route group (`/admin`) with magic link auth via Resend. |
| **Halls Router** | List dining halls, filter open-now, return hours + crowding | FastAPI router. Queries PostgreSQL for hall metadata + Redis for crowding snapshots. |
| **Menus Router** | Return menu for a given hall + date, trigger parse on cache miss | FastAPI router. Cache-aside pattern: check Redis, fallback to parser, persist to PostgreSQL + Redis. |
| **Crowding Router** | Accept location pings, return crowding levels | FastAPI router. Writes pings to Redis (2-min TTL). Reads aggregated crowding from Redis. |
| **Admin Router** | CRUD for hours/overrides, parser status | FastAPI router behind auth middleware. Magic link token validation. |
| **Service Layer** | Business logic decoupled from HTTP concerns | Python classes/functions. MenuService orchestrates cache-check + parser + persist. CrowdingService runs aggregation. |
| **PostgreSQL** | Persistent storage: halls, hours, overrides, menus | Railway-managed. Accessed via SQLModel ORM. Source of truth for all business data. |
| **Redis** | Fast ephemeral storage: menu cache, location pings, crowding snapshots | Railway-managed. Menu cache (30-min TTL), location pings (2-min TTL), crowding snapshots (60-sec TTL). |
| **Parsers** | Extract menu data from vendor websites | Python classes inheriting from abstract base. One per vendor: Sodexo, BonAppetit, Pomona. |
| **Vendor Websites** | External data sources for daily menus | Scraped on demand (cache miss). No official APIs. HTML parsing via httpx + BeautifulSoup or similar. |

## Recommended Project Structure

```
5c-menu/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory, lifespan, CORS
│   │   ├── config.py            # Pydantic BaseSettings (env vars)
│   │   ├── database.py          # SQLModel engine + session factory
│   │   ├── cache.py             # Redis client wrapper
│   │   ├── deps.py              # Shared FastAPI dependencies (get_db, get_redis)
│   │   │
│   │   ├── models/              # SQLModel ORM models (DB tables)
│   │   │   ├── __init__.py
│   │   │   ├── hall.py          # DiningHall model
│   │   │   ├── hours.py         # DiningHours, DiningHoursOverride
│   │   │   └── menu.py          # Menu model (JSONB stations)
│   │   │
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── hall.py          # HallResponse, HallListResponse
│   │   │   ├── menu.py          # MenuResponse, StationSchema
│   │   │   ├── crowding.py      # CrowdingResponse, LocationPing
│   │   │   └── admin.py         # HoursUpdate, OverrideCreate
│   │   │
│   │   ├── routers/             # FastAPI route handlers (thin)
│   │   │   ├── __init__.py
│   │   │   ├── halls.py         # GET /halls, GET /open-now
│   │   │   ├── menus.py         # GET /menus
│   │   │   ├── crowding.py      # GET /crowding, POST /location
│   │   │   └── admin.py         # Admin CRUD routes
│   │   │
│   │   ├── services/            # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── hall_service.py
│   │   │   ├── menu_service.py  # Cache-aside + parser orchestration
│   │   │   ├── crowding_service.py  # Aggregation + fallback logic
│   │   │   └── auth_service.py  # Magic link verification
│   │   │
│   │   ├── parsers/             # Vendor-specific menu scrapers
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Abstract MenuParser base class
│   │   │   ├── sodexo.py        # Hoch-Shanahan
│   │   │   ├── bonappetit.py    # Collins, Malott, McConnell
│   │   │   └── pomona.py        # Frank, Frary, Oldenborg
│   │   │
│   │   └── jobs/                # Background tasks
│   │       ├── __init__.py
│   │       └── aggregation.py   # Crowding aggregation (30-sec interval)
│   │
│   ├── tests/
│   │   ├── conftest.py          # Fixtures: test DB, test Redis, mock parsers
│   │   ├── test_halls.py
│   │   ├── test_menus.py
│   │   ├── test_crowding.py
│   │   ├── test_admin.py
│   │   └── parsers/
│   │       ├── fixtures/        # Saved HTML snapshots for parser tests
│   │       ├── test_sodexo.py
│   │       ├── test_bonappetit.py
│   │       └── test_pomona.py
│   │
│   ├── alembic/                 # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── alembic.ini
│   ├── pyproject.toml           # Python project config (dependencies, tools)
│   ├── Dockerfile
│   └── .env.example
│
├── web/
│   ├── app/                     # Next.js 14 App Router
│   │   ├── layout.tsx           # Root layout: providers (QueryClient, theme)
│   │   ├── page.tsx             # Home: hall list + "What's Open Now"
│   │   ├── hall/
│   │   │   └── [id]/
│   │   │       └── page.tsx     # Hall detail: meals, stations, items
│   │   └── admin/
│   │       ├── layout.tsx       # Auth-gated layout (magic link check)
│   │       ├── page.tsx         # Dashboard: parser status
│   │       ├── hours/
│   │       │   └── page.tsx     # Hours grid editor
│   │       └── overrides/
│   │           └── page.tsx     # Override management
│   │
│   ├── components/
│   │   ├── ui/                  # Generic UI primitives (Button, Badge, etc.)
│   │   ├── HallCard.tsx
│   │   ├── MenuDisplay.tsx
│   │   ├── MealTabs.tsx
│   │   ├── DateNavigation.tsx
│   │   └── CrowdingBadge.tsx
│   │
│   ├── hooks/
│   │   ├── useHalls.ts          # React Query: fetch halls
│   │   ├── useMenu.ts           # React Query: fetch menu by hall + date
│   │   └── useCrowding.ts       # React Query: fetch crowding levels
│   │
│   ├── lib/
│   │   ├── api.ts               # Fetch wrapper (base URL, error handling)
│   │   ├── queryClient.ts       # React Query client configuration
│   │   └── utils.ts             # Date formatting, time helpers
│   │
│   ├── types/
│   │   └── api.ts               # TypeScript types matching API response shapes
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── .env.example
│
├── mobile/                      # (Phase 3 — deferred)
│   └── .gitkeep
│
├── .gitignore
└── PRD.md
```

### Structure Rationale

- **`backend/app/`:** Nested under `app/` so `backend/tests/` and `backend/alembic/` sit at the same level as the application package. This is the standard FastAPI convention for larger projects and avoids import path confusion.
- **`models/` vs `schemas/` separation:** SQLModel models define database tables; Pydantic schemas define API request/response shapes. Keeping them separate prevents coupling the database schema to the API contract. SQLModel blurs this line by design, but explicit schemas give you freedom to evolve the API independently of the DB.
- **`routers/` (thin) + `services/` (thick):** Routers handle HTTP concerns (validation, status codes, response formatting). Services contain business logic (cache-aside orchestration, parser selection, crowding aggregation). This three-layer pattern (router -> service -> data) is the dominant FastAPI production pattern.
- **`parsers/` as its own package:** Parsers are the most change-prone code (vendor websites change without notice). Isolating them makes them independently testable with HTML fixture snapshots and prevents parser instability from leaking into service logic.
- **`web/types/api.ts`:** Manually maintained TypeScript types matching API responses. For this project size (7 endpoints), manual types are simpler than OpenAPI client generation. Consider auto-generation if the API grows past 15-20 endpoints.
- **`web/components/ui/`:** Generic UI primitives (Button, Card, Badge) separated from domain components (HallCard, MenuDisplay). Prevents domain logic from leaking into reusable UI.

## Architectural Patterns

### Pattern 1: Cache-Aside with Persistent Fallback

**What:** Check Redis cache first. On miss, run parser to fetch fresh data, write to both PostgreSQL (permanent) and Redis (TTL). On parser failure, fall back to last-good PostgreSQL data.

**When to use:** Every menu fetch request. This is the core data retrieval pattern.

**Trade-offs:**
- Pro: Fast reads (Redis), resilient to parser failures (PostgreSQL fallback), no scheduled jobs needed
- Con: First request after cache expiry is slow (parser runs synchronously). Acceptable for 30-min TTL with ~100-500 DAU.

**Example:**
```python
async def get_menu(hall_id: str, date: str, redis: Redis, db: AsyncSession) -> MenuResponse:
    cache_key = f"menu:{hall_id}:{date}"

    # 1. Check Redis
    cached = await redis.get(cache_key)
    if cached:
        return MenuResponse.model_validate_json(cached)

    # 2. Cache miss — run parser
    parser = get_parser_for_hall(hall_id)
    try:
        menu = await parser.parse(date)
    except ParserError:
        # 3. Parser failed — fall back to PostgreSQL
        menu = await db.exec(
            select(Menu).where(Menu.hall_id == hall_id, Menu.date == date)
        )
        if menu:
            return MenuResponse.from_orm(menu)
        raise HTTPException(503, "Menu unavailable")

    # 4. Persist + cache
    db.add(Menu(hall_id=hall_id, date=date, stations=menu.stations))
    await db.commit()
    await redis.setex(cache_key, 1800, menu.model_dump_json())

    return menu
```

### Pattern 2: Abstract Parser with Vendor Implementations

**What:** Base class defines the parser interface (`parse(date) -> list[Station]`). Each vendor subclass handles its own HTML structure, URL patterns, and data normalization.

**When to use:** All three dining vendors (Sodexo, Bon Appetit, Pomona). Adding a new vendor means adding one file.

**Trade-offs:**
- Pro: Vendor changes isolated to one file. Parser tests use saved HTML fixtures, so they run fast and don't hit the network.
- Con: Slight abstraction overhead. Worth it given that vendor websites change unpredictably (this is the most brittle part of the system).

**Example:**
```python
class MenuParser(ABC):
    @abstractmethod
    async def parse(self, hall_id: str, date: str) -> list[Station]:
        """Fetch and parse menu for a specific hall and date."""
        ...

    @abstractmethod
    def supports_hall(self, hall_id: str) -> bool:
        """Whether this parser handles the given hall."""
        ...

class BonAppetitParser(MenuParser):
    HALL_IDS = {"collins", "malott", "mcconnell"}
    BASE_URL = "https://bamco.cafebonappetit.com/..."

    async def parse(self, hall_id: str, date: str) -> list[Station]:
        html = await self._fetch(self._build_url(hall_id, date))
        return self._extract_stations(html)

    def supports_hall(self, hall_id: str) -> bool:
        return hall_id in self.HALL_IDS
```

### Pattern 3: Ephemeral Session Aggregation (Crowding)

**What:** Location pings stored as individual Redis keys with short TTLs. Aggregation job scans all active sessions, applies geofence matching, counts per hall, writes crowding snapshot. Sessions self-expire.

**When to use:** Crowding feature (Phase 4). The pattern extends naturally to any real-time counting use case.

**Trade-offs:**
- Pro: Zero persistent state for location data (privacy-preserving). Redis TTL handles cleanup automatically. No background worker needed for session expiry.
- Con: Redis SCAN for active sessions is O(N) where N = total keys. Fine at 500 DAU (~50 concurrent sessions). Would need Redis Sets or sorted sets at 10K+ concurrent sessions.

## Data Flow

### Menu Request Flow

```
[User opens hall page]
    |
    v
[React Query: useMenu(hallId, date)]
    |
    v
[GET /api/v2/menus?hall={id}&date={date}]
    |
    v
[Menus Router] --> [MenuService.get_menu()]
                        |
                        ├── [Redis.get("menu:{id}:{date}")]
                        |       |
                        |       ├── HIT --> return cached JSON
                        |       |
                        |       └── MISS --> continue
                        |
                        ├── [Parser.parse(id, date)]
                        |       |
                        |       ├── SUCCESS --> structured menu data
                        |       |
                        |       └── FAILURE --> PostgreSQL fallback
                        |
                        ├── [PostgreSQL: INSERT/UPSERT menu]
                        |
                        └── [Redis: SETEX with 30-min TTL]
                                |
                                v
                        [Return MenuResponse to client]
```

### Crowding Data Flow (Phase 4)

```
[Mobile app: foreground, location granted]
    |
    v (every 30 sec)
[POST /api/v2/location {session_id, lat, lng}]
    |
    v
[Crowding Router] --> [Redis: SETEX "location:{session_id}" TTL=120s]


[Aggregation Job: runs every 30 seconds]
    |
    v
[Redis: SCAN "location:*"] --> [list of active sessions with coords]
    |
    v
[For each hall: count sessions within geofence radius]
    |
    v
[Apply thresholds: <15 not_busy, 15-40 moderate, >40 busy]
    |
    v
[Redis: SETEX "crowding:{hall_id}" TTL=60s]


[Client: GET /api/v2/crowding]
    |
    v
[Crowding Router] --> [Redis: MGET "crowding:*"] --> [Return all hall levels]
```

### Admin Data Flow

```
[Admin: navigates to /admin]
    |
    v
[Magic link auth: email --> Resend --> click link --> JWT token]
    |
    v
[Authenticated admin session]
    |
    v
[POST /api/v2/admin/halls/{id}/hours]
    |
    v
[Admin Router] --> [Auth middleware: verify JWT]
                        |
                        v
                   [HallService.update_hours()]
                        |
                        v
                   [PostgreSQL: UPDATE dining_hours]
                        |
                        v
                   [Redis: DEL related cache keys (hours changed)]
```

### Key Data Flows

1. **Menu fetch (hot path):** Client -> React Query -> API -> Redis (cache hit 95%+ of requests) -> Client. Cache miss triggers parser -> PostgreSQL persist -> Redis cache -> Client. The 30-min TTL means most users hit warm cache.
2. **Hall list + open-now:** Client -> API -> PostgreSQL (hall metadata) + Redis (crowding snapshots) -> merged response. Lightweight query, no parser involvement.
3. **Location ping (write-heavy):** Mobile -> API -> Redis SET with TTL. No PostgreSQL writes. No response body needed (204 No Content). Designed for high throughput, low latency.
4. **Crowding aggregation:** Background job -> Redis SCAN -> geofence calculation -> Redis SET. Pure Redis operation. If insufficient data, schedule-based fallback calculated in-process (no DB hit).

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-500 DAU (launch) | Single FastAPI process, single Redis, single PostgreSQL. On-demand parsing. No background workers needed except crowding aggregation (simple `asyncio.create_task` loop). Everything fits in Railway's starter tier. |
| 500-5K DAU | Add parser pre-warming: background task fetches all 7 halls x 3 meals at 6am daily so cache is warm before breakfast rush. Move crowding aggregation to a proper background task (APScheduler or FastAPI lifespan task). Monitor Redis memory (location pings at 5K DAU = ~500 concurrent keys, ~50KB). |
| 5K-50K DAU | Split API and worker processes. Add connection pooling for PostgreSQL (asyncpg pool). Consider Redis Cluster if key count exceeds single-node memory. At this scale you likely need a CDN for the web frontend (Vercel handles this). Parser rate limiting becomes important to avoid being blocked by vendor sites. |

### Scaling Priorities

1. **First bottleneck — parser latency on cache miss:** A cold cache fetch (HTML scrape + parse) takes 1-5 seconds. At launch this is fine (30-min TTL means most hits are warm). Fix: pre-warm cache with a daily background job fetching all menus at 5-6am.
2. **Second bottleneck — crowding aggregation at scale:** Redis SCAN becomes slow with thousands of location keys. Fix: use Redis Sets per hall (`hall_sessions:{hall_id}` with session members) instead of individual keys. Count via SCARD instead of SCAN + distance calculation.

## Anti-Patterns

### Anti-Pattern 1: Scheduled Parser Jobs Instead of Cache-Aside

**What people do:** Run a cron job every 30 minutes to scrape all menus and populate the cache/database proactively.
**Why it's wrong:** Wastes resources scraping menus nobody is viewing (e.g., Oldenborg at 8pm, breakfast menus after 11am). Creates a dependency on a scheduler infrastructure. If the job fails, stale data persists until the next run with no automatic retry.
**Do this instead:** Cache-aside pattern. Parse on demand when a user actually requests data and the cache is cold. The first user after TTL expiry pays the latency cost; everyone else gets cached data. Add pre-warming only when you have evidence of cold-cache latency complaints.

### Anti-Pattern 2: Storing Location Data in PostgreSQL

**What people do:** Write every location ping to a PostgreSQL table for "analytics later."
**Why it's wrong:** Location pings at 1 per 30 seconds per active user generate massive write volume. PostgreSQL is not designed for this write pattern. It also creates a privacy liability — persistent location data requires stronger data protection measures.
**Do this instead:** Redis-only for location pings (2-min TTL, auto-expire). Aggregated crowding counts (not raw locations) can optionally be persisted for historical analysis, but raw pings should never touch PostgreSQL.

### Anti-Pattern 3: Shared Component Library Between Web and Mobile

**What people do:** Create a `shared/` or `packages/components/` directory with React components used by both Next.js and Expo.
**Why it's wrong:** React (web) and React Native (mobile) have fundamentally different rendering primitives (`<div>` vs `<View>`, CSS vs StyleSheet). Shared components either become lowest-common-denominator abstractions or require platform-specific code paths that negate the sharing benefit. It also couples the web and mobile release cycles.
**Do this instead:** Share types, API client logic, and business constants (hall IDs, school colors, threshold values). Do not share UI components. Each platform should have its own component implementations optimized for its rendering model. A `shared/` directory for types/constants/API client is fine; a shared component library is not.

### Anti-Pattern 4: SSR for Dynamic Menu Data

**What people do:** Use Next.js Server Components or `getServerSideProps` to fetch menu data at request time on the server.
**Why it's wrong:** Menu data changes at most every 30 minutes (cache TTL). Server-rendering it adds latency to every page load, couples the Vercel deployment to the Railway backend availability, and prevents client-side caching via React Query. It also makes the Vercel <-> Railway network hop part of the critical rendering path.
**Do this instead:** Client-side rendering with React Query. The page shell loads instantly from Vercel (static HTML + JS), then React Query fetches menu data from the API. React Query's built-in caching, stale-while-revalidate, and retry logic handle all the edge cases that SSR would need custom implementation for.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Sodexo website | HTTP scrape (httpx) on cache miss | HTML structure changes without notice. Parser tests must use saved fixtures. Add user-agent header to avoid blocks. |
| Bon Appetit website | HTTP scrape (httpx) on cache miss | Serves 3 halls (Collins, Malott, McConnell). Same parser, different hall IDs in URL. May have a JSON API behind the scenes — investigate during implementation. |
| Pomona dining website | HTTP scrape (httpx) on cache miss | Serves 3 halls (Frank, Frary, Oldenborg). Different site structure from Bon Appetit. |
| Resend (email) | REST API call for magic link delivery | Single admin email hardcoded. Low volume (admin login only). Free tier sufficient. |
| Railway (PostgreSQL) | SQLModel + asyncpg connection string from env var | Managed service. Connection pooling via SQLModel/SQLAlchemy engine pool. |
| Railway (Redis) | redis-py async client, connection string from env var | Managed service. Single Redis instance serves cache, location pings, and crowding snapshots. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Web frontend <-> Backend API | HTTPS REST (JSON). React Query manages request lifecycle. | CORS configured for Vercel domain + localhost. API base URL from env var. |
| Mobile app <-> Backend API | HTTPS REST (JSON). Same API as web. | No CORS needed (native HTTP). Same React Query hooks (shared patterns, not shared code). |
| Admin panel <-> Backend API | HTTPS REST (JSON) with JWT auth header. | Magic link flow: admin clicks email link -> frontend stores JWT -> all admin API calls include Authorization header. |
| Router <-> Service | Direct Python function call. Service receives DB session + Redis client via dependency injection. | Routers are thin (validate input, call service, format response). Services contain all business logic. |
| Service <-> Parser | Direct Python function call. Service selects parser based on hall's `parser_type` field. | Parser returns structured data (list of Station objects). Service handles caching, persistence, error fallback. |
| Service <-> PostgreSQL | SQLModel ORM via async session. | All DB access goes through services, never directly from routers. |
| Service <-> Redis | redis-py async client. Key naming convention: `{resource}:{identifier}`. | All Redis access goes through services. Cache key format documented in service layer. |

## Build Order (Dependencies Between Components)

The following build order reflects hard dependencies — each layer requires the previous layer to function.

### Phase 1a: Backend Foundation (build first)
1. **Config + Database setup** (config.py, database.py, deps.py) — everything depends on this
2. **SQLModel models** (hall.py, hours.py, menu.py) — defines the data shape
3. **DB migrations** (Alembic) — creates tables, seeds hall data
4. **Redis client** (cache.py) — needed for menu caching

### Phase 1b: Parsers (build second, depends on models)
5. **Base parser class** (parsers/base.py) — defines interface
6. **One parser** (e.g., bonappetit.py) — prove the pattern with the vendor serving 3 halls
7. **Parser tests with fixtures** — save HTML snapshots, test parsing logic
8. **Remaining parsers** (sodexo.py, pomona.py) — follow established pattern

### Phase 1c: API Layer (build third, depends on parsers + models)
9. **MenuService** (cache-aside logic) — orchestrates Redis + parser + PostgreSQL
10. **HallService** (hall list, open-now filtering) — queries PostgreSQL for metadata
11. **Menus router + Halls router** — thin HTTP layer over services
12. **API integration tests** — test full request/response cycle

### Phase 1d: Web Frontend (build fourth, depends on API)
13. **API client + types** (lib/api.ts, types/api.ts) — typed fetch wrapper
14. **React Query hooks** (useHalls, useMenu) — data fetching layer
15. **Hall list page** (page.tsx) — home screen with hall cards
16. **Hall detail page** (hall/[id]/page.tsx) — menu display with meal tabs
17. **Date navigation, dark mode** — UI polish

### Phase 1e: Admin Panel (build fifth, depends on API + additional endpoints)
18. **Auth service** (magic link via Resend) — admin login flow
19. **Admin router** (hours CRUD, parser status) — protected endpoints
20. **Admin frontend** (hours editor, override manager) — web UI under /admin

### Phase 4 (later): Crowding System
21. **Location ping endpoint** — write to Redis
22. **Aggregation job** — background task scanning Redis
23. **Crowding service + router** — read aggregated data
24. **Mobile app with location** — Expo + expo-location

**Key dependency insight:** The backend must be functional (API returning real data) before the frontend can be meaningfully developed. Building parsers before the API layer ensures real data flows through from day one, avoiding mock-data drift. The admin panel depends on the same API but adds auth, so it can be built last in Phase 1.

## Sources

- [FastAPI Best Practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) — Project structure, layered architecture patterns. **MEDIUM confidence** (community best practices, widely cited).
- [FastAPI Official Docs: Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — Router organization, dependency injection. **HIGH confidence** (official documentation).
- [Building a Scalable FastAPI Application with SQLModel (Medium)](https://medium.com/@faizulkhan56/building-a-scalable-fastapi-application-with-sqlmodel-a-complete-guide-to-three-layer-architecture-3c33ec981922) — Three-layer architecture with SQLModel. **MEDIUM confidence** (tutorial, aligns with official patterns).
- [Generating API clients in monorepos with FastAPI & Next.js (Vinta)](https://www.vintasoftware.com/blog/nextjs-fastapi-monorepo) — Monorepo structure, OpenAPI client generation. **MEDIUM confidence** (production experience report).
- [Vertical Monorepo Architecture for FastAPI (LSST)](https://sqr-075.lsst.io/) — Shared model patterns, monorepo packaging. **MEDIUM confidence** (real-world production system).
- [CampusDish API (GitHub)](https://github.com/stevenleeg/campusdish_api) — College dining API architecture reference: scraper + PostgreSQL + Flask. **LOW confidence** (small project, but validates the scraper -> DB -> API pattern).
- [Yoki - York University API (GitHub)](https://github.com/SSADC-at-york/Yoki) — University data scraper architecture. **LOW confidence** (reference only).
- [TanStack Query: Advanced SSR](https://tanstack.com/query/latest/docs/framework/react/guides/advanced-ssr) — React Query with Next.js App Router. **HIGH confidence** (official TanStack documentation).
- [FastAPI Best Practices for Production 2026 (FastLaunchAPI)](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026) — Production patterns. **MEDIUM confidence** (aligns with community consensus).
- [Cache Aside Pattern in Web Scraping (ScrapFly)](https://scrapfly.io/blog/posts/how-to-use-cache-in-web-scraping) — Cache-aside implementation for scrapers. **MEDIUM confidence** (well-documented pattern).

---
*Architecture research for: 5C Menu App — College dining menu aggregation*
*Researched: 2026-02-07*
