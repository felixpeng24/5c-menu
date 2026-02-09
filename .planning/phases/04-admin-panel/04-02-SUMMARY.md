---
phase: 04-admin-panel
plan: 02
subsystem: api
tags: [fastapi, crud, sqlmodel, sqlalchemy, parser-health, instrumentation]

# Dependency graph
requires:
  - phase: 04-admin-panel/01
    provides: "Admin router, require_admin dependency, ParserRun model, admin schemas"
provides:
  - "Hours CRUD endpoints (GET/POST/PUT/DELETE /api/v2/admin/hours)"
  - "Overrides CRUD endpoints (GET/POST/PUT/DELETE /api/v2/admin/overrides)"
  - "Parser health endpoint (GET /api/v2/admin/health)"
  - "Parser execution instrumentation in get_menu_with_fallback"
affects: [04-03, 04-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [crud-endpoints, aggregation-query, best-effort-telemetry]

key-files:
  created: []
  modified:
    - backend/app/routers/admin.py
    - backend/app/parsers/fallback.py

key-decisions:
  - "Time/date fields serialized as ISO strings via isoformat() and parsed via fromisoformat()"
  - "Parser instrumentation is best-effort telemetry -- wrapped in try/except to never break menu flow"
  - "Health endpoint uses SQLAlchemy func/case aggregation over 24-hour window"

patterns-established:
  - "CRUD endpoint pattern: helper function converts SQLModel to Pydantic response schema"
  - "Best-effort telemetry: _record_run wraps ParserRun creation so failures never break core flow"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 4 Plan 2: Admin CRUD Endpoints and Parser Health Summary

**Hours/overrides CRUD (8 endpoints) plus parser health aggregation and fallback execution instrumentation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T10:32:39Z
- **Completed:** 2026-02-09T10:35:03Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Full CRUD for dining hours: GET/POST/PUT/DELETE with ISO time serialization
- Full CRUD for dining hours overrides: GET/POST/PUT/DELETE with date/time parsing
- Parser health endpoint returning per-hall summary (last_success, total_runs, error_count, error_rate)
- Instrumented get_menu_with_fallback to record ParserRun entries on every execution
- All 90 existing tests still pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Hours and overrides CRUD endpoints** - `3d3b552` (feat)
2. **Task 2: Parser health endpoint and fallback instrumentation** - `ccd51a1` (feat)

## Files Created/Modified
- `backend/app/routers/admin.py` - Added 8 CRUD endpoints (hours + overrides), health aggregation endpoint, helper converters
- `backend/app/parsers/fallback.py` - Added _record_run helper and instrumented get_menu_with_fallback to record ParserRun entries

## Decisions Made
- Time/date serialization uses isoformat()/fromisoformat() consistently (ISO 8601 strings in API, native types in DB)
- Parser instrumentation is best-effort: wrapped in try/except so recording failures never break the menu fetch flow
- Health endpoint computes error_rate as percentage (error_count/total_runs*100) with one decimal place
- ParserRun commits are separate transactions from menu persistence (telemetry decoupled from core data)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All admin API endpoints complete: auth (plan 01), hours CRUD, overrides CRUD, parser health
- Frontend admin pages (plans 03-04) can now consume these endpoints
- Parser health data will accumulate as parsers run through get_menu_with_fallback

## Self-Check: PASSED

- All 2 claimed files exist on disk
- Commit `3d3b552` (Task 1) found in git log
- Commit `ccd51a1` (Task 2) found in git log

---
*Phase: 04-admin-panel*
*Completed: 2026-02-09*
