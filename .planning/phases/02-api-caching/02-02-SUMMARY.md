---
phase: 02-api-caching
plan: 02
subsystem: api
tags: [redis, caching, asyncio, coalescing, fastapi, menu-service]

# Dependency graph
requires:
  - phase: 01-parsers-data-models
    provides: "BaseParser, SodexoParser, BonAppetitParser, PomonaParser, fallback orchestrator"
  - phase: 02-api-caching
    plan: 01
    provides: "FastAPI app, Redis lifecycle, dependencies, MenuResponse schema"
provides:
  - "Redis cache get/set with jittered TTL (25-35 min)"
  - "In-process request coalescing via asyncio.Future"
  - "Menu service orchestrating cache -> coalesce -> parser -> fallback -> cache write"
  - "GET /api/v2/menus endpoint with input validation"
  - "Hall config and parser registry for all 7 dining halls"
affects: [02-04, 03-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns: [cache-aside-with-jitter, request-coalescing, service-layer-orchestration]

key-files:
  created:
    - backend/app/services/__init__.py
    - backend/app/services/cache.py
    - backend/app/services/coalesce.py
    - backend/app/services/menu_service.py
    - backend/app/routers/menus.py
  modified:
    - backend/app/main.py

key-decisions:
  - "Cache-aside pattern with jittered TTL (BASE_TTL=1800s +/- 300s) prevents thundering herd"
  - "Request coalescing uses asyncio.Future with 30s timeout for stampede prevention"
  - "Hall config and parser registry centralized in menu_service.py (not database-driven)"

patterns-established:
  - "Service layer pattern: routers call services, services orchestrate cache/parsers/DB"
  - "Cache-aside: check cache -> coalesced miss handler -> cache write"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 2 Plan 2: Cache Layer & Menus Endpoint Summary

**Redis cache-aside with jittered TTL, asyncio request coalescing, and GET /api/v2/menus endpoint serving all 7 halls**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T05:33:48Z
- **Completed:** 2026-02-09T05:35:53Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Redis cache layer with get/set and jittered TTL (25-35 min range) to prevent synchronized expiration
- In-process request coalescing using asyncio.Future prevents stampede on concurrent cache misses
- Menu service orchestrates full pipeline: cache check -> coalesced fetch -> parser via fallback -> cache write
- GET /api/v2/menus endpoint with hall_id/date/meal validation, returning MenuResponse

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cache service, coalescing, and menu service** - `8d974ba` (feat)
2. **Task 2: Create menus router and wire into FastAPI app** - `54d06fc` (feat)

## Files Created/Modified
- `backend/app/services/__init__.py` - Services package init
- `backend/app/services/cache.py` - Redis cache get/set with jittered TTL
- `backend/app/services/coalesce.py` - Asyncio.Future-based request coalescing with 30s timeout
- `backend/app/services/menu_service.py` - Menu fetch orchestration, hall config, parser registry
- `backend/app/routers/menus.py` - GET / endpoint with input validation and error handling
- `backend/app/main.py` - Added menus router at /api/v2/menus

## Decisions Made
- Cache-aside with jittered TTL (1800 +/- 300 seconds) prevents thundering herd without complex distributed locking
- Request coalescing centralizes in-process deduplication via module-level dict of asyncio.Future objects
- Hall config and parser registry are in-code dicts (not DB-driven) since the 7 halls are static

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Menus endpoint fully operational, ready for frontend integration
- Cache layer ready for plan 02-04 (cache warming / management)
- All 7 halls mapped to their parsers and accessible via single endpoint

## Self-Check: PASSED

All 5 created files verified on disk. Both task commits (8d974ba, 54d06fc) verified in git log.

---
*Phase: 02-api-caching*
*Completed: 2026-02-09*
