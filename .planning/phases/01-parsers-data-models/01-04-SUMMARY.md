---
phase: 01-parsers-data-models
plan: 04
subsystem: parsing, database
tags: [pomona, eatec-json, fallback, httpx, selectolax, dietary-tags, station-filters]

requires:
  - phase: 01-01
    provides: BaseParser ABC, ParsedMenu models, POMONA_FILTER config, dietary tag normalization, Menu SQLModel table
provides:
  - PomonaParser implementation for Frank, Frary, Oldenborg with dynamic JSON URL discovery
  - Fallback orchestrator (persist_menu, load_latest_menu, get_menu_with_fallback)
  - Synthetic test fixtures for all 3 Pomona halls
  - 15 Pomona parser unit tests covering all edge cases
  - 8 fallback orchestrator unit tests with mocked sessions
affects: [02-api, 03-frontend]

tech-stack:
  added: []
  patterns: [two-step fetch for dynamic URL discovery, dict-to-list normalization for single-item edge cases, comma+slash splitting for Oldenborg]

key-files:
  created:
    - backend/app/parsers/pomona.py
    - backend/app/parsers/fallback.py
    - backend/tests/test_pomona_parser.py
    - backend/tests/test_fallback.py
    - backend/tests/fixtures/pomona/frank_2026-02-07.json
    - backend/tests/fixtures/pomona/frary_2026-02-07.json
    - backend/tests/fixtures/pomona/oldenborg_2026-02-07.json
    - backend/tests/fixtures/pomona/frank_page.html
  modified: []

key-decisions:
  - "Used synthetic fixtures (not live fetches) since Pomona eatec JSON URL redirects to auth portal"
  - "Exposed discover_json_url as a public method for testability of two-step fetch logic"
  - "Used datetime.now(timezone.utc) instead of deprecated datetime.utcnow()"

patterns-established:
  - "Two-step fetch: page HTML -> discover JSON URL from data attribute -> fetch JSON (resilient to URL changes)"
  - "Dict-to-list normalization: check isinstance(recipes, dict) and wrap in list for single-item edge cases"
  - "Fallback orchestrator: try live parser -> persist on success -> load last-known-good on failure"

duration: 5min
completed: 2026-02-07
---

# Phase 1 Plan 4: Pomona Parser & Fallback Orchestrator Summary

**PomonaParser with dynamic JSON URL discovery for Frank/Frary/Oldenborg, Oldenborg comma+slash splitting, single-item recipe handling, and fallback orchestrator returning last-known-good PostgreSQL data on parser failure**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-08T01:08:50Z
- **Completed:** 2026-02-08T01:14:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- PomonaParser with two-step fetch (page HTML -> JSON URL -> JSON data) for all 3 Pomona dining halls
- EatecExchange JSON parsing with single-item recipe dict-to-list normalization, dietary tag extraction, and station merging via POMONA_FILTER
- Oldenborg-specific comma+slash item splitting (other halls comma-only)
- Fallback orchestrator: persists fresh data to Menu table, loads last-known-good when parser fails, returns (None, True, None) when no stored data exists
- 23 total tests passing (15 parser + 8 fallback) with zero network calls

## Task Commits

Each task was committed atomically:

1. **Task 1: PomonaParser with dynamic JSON URL discovery and fixtures** - `d4a147b` (feat)
2. **Task 2: Fallback orchestrator and all unit tests** - `fa1a9fb` (feat)

## Files Created/Modified
- `backend/app/parsers/pomona.py` - PomonaParser(BaseParser) with two-step fetch, EatecExchange parsing, Oldenborg splitting
- `backend/app/parsers/fallback.py` - persist_menu, load_latest_menu, get_menu_with_fallback orchestrator
- `backend/tests/test_pomona_parser.py` - 15 tests: all halls, single-item, splitting, ordering, tags, closed, URL discovery
- `backend/tests/test_fallback.py` - 8 tests: persist/load round-trip, parser failure fallback, no stored data, fresh persistence
- `backend/tests/fixtures/pomona/frank_2026-02-07.json` - Synthetic Frank fixture (3 meals, multiple stations, dietary tags)
- `backend/tests/fixtures/pomona/frary_2026-02-07.json` - Synthetic Frary fixture (includes single-item dict edge case in Dinner)
- `backend/tests/fixtures/pomona/oldenborg_2026-02-07.json` - Synthetic Oldenborg fixture (slash+comma items)
- `backend/tests/fixtures/pomona/frank_page.html` - Minimal HTML with data-dining-menu-json-url attribute

## Decisions Made
- Created synthetic fixtures rather than fetching live data since Pomona eatec JSON URL redirects to an auth portal
- Exposed `discover_json_url()` as a public method on PomonaParser for direct testability of the URL discovery logic
- Used `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()` in fallback orchestrator
- Used unittest.mock for fallback tests (mocking AsyncSession) rather than in-memory SQLite, as async SQLite testing would add unnecessary complexity

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed deprecated datetime.utcnow() usage**
- **Found during:** Task 2 (fallback tests)
- **Issue:** `datetime.datetime.utcnow()` is deprecated in Python 3.12 and scheduled for removal
- **Fix:** Changed all 3 occurrences to `datetime.datetime.now(datetime.timezone.utc)`
- **Files modified:** backend/app/parsers/fallback.py
- **Verification:** All tests pass without deprecation warnings
- **Committed in:** fa1a9fb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor fix for Python 3.12 compatibility. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 7 dining halls now have parser implementations: Sodexo (Hoch), Bon Appetit (Collins, Malott, McConnell), Pomona (Frank, Frary, Oldenborg)
- Fallback orchestrator ready to wrap any parser for production use
- Phase 1 parser suite complete; ready for Phase 2 API development
- All parsers importable together: SodexoParser, BonAppetitParser, PomonaParser, get_menu_with_fallback

## Self-Check: PASSED

- All 2 key files verified on disk (pomona.py, fallback.py)
- 2 commits found matching "01-04" pattern (d4a147b, fa1a9fb)

---
*Phase: 01-parsers-data-models*
*Completed: 2026-02-07*
