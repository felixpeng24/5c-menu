# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Students can quickly see what's being served at every dining hall right now, so they can decide where to eat.
**Current focus:** Phase 4 (Admin Panel) - auth foundation complete, CRUD endpoints next

## Current Position

Phase: 4 of 4 (Admin Panel)
Plan: 1 of 4 in current phase
Status: Plan 04-01 complete (auth foundation)
Last activity: 2026-02-09 -- Completed 04-01 (admin auth, ParserRun model, schemas)

Progress: [████████████████░░░░] 82%

## Performance Metrics

**Velocity:**
- Total plans completed: 14
- Average duration: 3 min
- Total execution time: 40 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-parsers-data-models | 4/4 | 19 min | ~5 min |
| 02-api-caching | 4/4 | 5 min | ~1 min |
| 03-web-frontend | 5/5 | 14 min | ~3 min |
| 04-admin-panel | 1/4 | 2 min | ~2 min |

**Recent Trend:**
- Last 5 plans: 2m, 2m, 2m, 1m, 2m
- Trend: stable/fast

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 4 phases derived from requirement clusters (Parsers, API, Frontend, Admin)
- Roadmap: Phases 3 and 4 both depend on Phase 2, could run in parallel
- 01-01: Used `import datetime as _dt` aliasing to avoid Pydantic 2.12 field name clash with `date` type + `UniqueConstraint`
- 01-01: `stations_json` typed as `Any` with `sa_column=Column(JSON)` for SQLModel 0.0.32 / Pydantic 2.12 compatibility
- 01-01: Station filter pipeline uses dict-based merge preserving insertion order
- 01-01: Dietary tag normalization maps to lowercase canonical strings (not enum values)
- 01-02: Sodexo parser uses live JSON-in-HTML extraction from nutData div
- 01-03: BAMCO parser uses regex extraction of Bamco.menu_items + Bamco.dayparts from inline JS (legacy JSON API confirmed dead, 403)
- 01-04: Pomona parser uses synthetic fixtures (live site requires auth); fallback orchestrator uses mock-based tests
- 01-04: Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`
- 02-01: Redis managed via FastAPI lifespan context manager, not module-level singleton
- 02-01: Dependencies re-exported through app.dependencies for single import point
- 02-01: Response schemas use Pydantic BaseModel (not SQLModel) for API contracts
- 02-02: Cache-aside pattern with jittered TTL (1800s +/- 300s) prevents thundering herd
- 02-02: Request coalescing uses asyncio.Future with 30s timeout for stampede prevention
- 02-02: Hall config and parser registry centralized in menu_service.py (not database-driven)
- 02-03: Override precedence: start_time=None means closed, override times replace regular, override-only entries are special openings
- 02-03: Service layer pattern: business logic in app/services/, routers delegate to service functions
- 02-03: Testability via now_override parameter instead of mocking datetime.now
- 02-04: Integration tests use dependency_overrides with fakeredis + in-memory SQLite (no external services)
- 02-04: Menu tests mock parser fetch_and_parse to return None, testing DB fallback path
- 02-04: Upgraded pytest-asyncio to 0.25.3 for modern async fixture support
- 03-01: Tailwind v4 CSS-first config via @theme in globals.css (no tailwind.config.ts)
- 03-01: QueryProvider uses useState pattern to avoid recreating QueryClient on re-renders
- 03-01: useOpenNow polls every 60s; useHalls has 5min staleTime for rarely-changing metadata
- 03-01: TypeScript interfaces in types.ts match backend Pydantic schemas exactly
- 03-02: COLLEGE_BG lookup map for school colors (no dynamic Tailwind classes)
- 03-02: MealTabs uses useMenu hook with inline stale indicator (replaced by StaleBanner in 03-04)
- 03-03: DateBar uses Pacific timezone via America/Los_Angeles for "today" computation
- 03-03: StaleBanner uses native Intl.RelativeTimeFormat (no date-fns dependency)
- 03-04: Open-now filter only applies when selected date is Pacific today
- 03-04: Sticky header with backdrop-blur, max-w-lg mobile-first layout
- 03-05: 17 component tests across 5 files, HallCard tests use QueryClientProvider wrapper
- 04-01: PyJWT for magic link JWT creation/verification (HS256, 15min expiry for links, 7day for sessions)
- 04-01: Anti-enumeration pattern: POST /auth/request-link always returns 200 regardless of email match
- 04-01: Session stored in httpOnly secure cookie (samesite=lax), require_admin FastAPI dependency for auth gate
- 04-01: ParserRun model uses string status field (not enum) for flexibility

### Pending Todos

None.

### Blockers/Concerns

- Pomona JSON URL discovery needs runtime validation -- synthetic fixtures used for testing, live site may redirect to auth portal
- BAMCO fixture files are large (~1-1.5 MB each) -- consider .gitignore if repo size is a concern

## Session Continuity

Last session: 2026-02-09
Stopped at: Completed 04-01-PLAN.md (admin auth foundation)
Resume file: None
