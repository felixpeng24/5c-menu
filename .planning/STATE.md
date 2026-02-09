# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Students can quickly see what's being served at every dining hall right now, so they can decide where to eat.
**Current focus:** Phase 2 in progress (API & Caching)

## Current Position

Phase: 2 of 4 (API & Caching)
Plan: 3 of 4 in current phase
Status: Plans 02-01, 02-02, 02-03 complete, executing phase 2
Last activity: 2026-02-09 -- Completed 02-03 (hours service, open-now endpoint)

Progress: [████████████░░░░░░░░] 31%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 4 min
- Total execution time: 21 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-parsers-data-models | 4/4 | 19 min | ~5 min |
| 02-api-caching | 1/4 | 2 min | ~2 min |

**Recent Trend:**
- Last 5 plans: 4m, 5m, 5m, 2m
- Trend: stable

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
- 02-03: Override precedence: start_time=None means closed, override times replace regular, override-only entries are special openings
- 02-03: Service layer pattern: business logic in app/services/, routers delegate to service functions
- 02-03: Testability via now_override parameter instead of mocking datetime.now

### Pending Todos

None.

### Blockers/Concerns

- Pomona JSON URL discovery needs runtime validation -- synthetic fixtures used for testing, live site may redirect to auth portal
- BAMCO fixture files are large (~1-1.5 MB each) -- consider .gitignore if repo size is a concern

## Session Continuity

Last session: 2026-02-09
Stopped at: Completed 02-03-PLAN.md (hours service, open-now endpoint)
Resume file: None
