---
phase: 01-parsers-data-models
plan: 01
subsystem: database, parsing
tags: [sqlmodel, pydantic, alembic, asyncpg, httpx, selectolax, station-filters, dietary-tags]

requires:
  - phase: none
    provides: first plan in project
provides:
  - SQLModel Menu and DiningHall table models with JSONB stations column
  - ParsedMenu/ParsedMeal/ParsedStation/ParsedMenuItem Pydantic interchange models
  - BaseParser ABC with fetch_raw/parse separation
  - Station filter configs for Sodexo, Bon Appetit, and Pomona vendors
  - Dietary tag normalization across all 3 vendors
  - Sodexo station name normalization helper
  - Async database engine and session factory
  - Alembic migration infrastructure
affects: [01-02, 01-03, 01-04, 02-api]

tech-stack:
  added: [sqlmodel 0.0.32, httpx 0.28.1, selectolax 0.4.6, asyncpg, pydantic-settings, alembic, beautifulsoup4, psycopg2-binary, pytest, pytest-asyncio]
  patterns: [fetch/parse separation, data-driven station filter configs, Pydantic interchange models]

key-files:
  created:
    - backend/pyproject.toml
    - backend/app/config.py
    - backend/app/db.py
    - backend/app/models/enums.py
    - backend/app/models/dining_hall.py
    - backend/app/models/menu.py
    - backend/app/parsers/base.py
    - backend/app/parsers/station_filters.py
    - backend/alembic.ini
    - backend/alembic/env.py
    - backend/tests/conftest.py
  modified: []

key-decisions:
  - "Used import datetime as _dt aliasing in menu.py to avoid Pydantic field name clash with date type when combined with UniqueConstraint"
  - "stations_json typed as Any with sa_column=Column(JSON) for SQLModel/Pydantic 2.12 compatibility"
  - "Station filter pipeline uses dict-based merge preserving insertion order for correct canonical station deduplication"
  - "Dietary tag normalization maps to lowercase canonical strings (not enum values) for flexibility"

patterns-established:
  - "Fetch/parse separation: BaseParser.fetch_raw() handles I/O, parse() is pure and testable against fixtures"
  - "Data-driven station filters: StationFilterConfig dataclass consumed by apply_station_filters pipeline"
  - "Pydantic interchange models: ParsedMenu hierarchy separate from SQLModel table models"

duration: 5min
completed: 2026-02-07
---

# Phase 1 Plan 1: Project Setup & Data Models Summary

**SQLModel Menu/DiningHall tables with JSONB stations, BaseParser ABC enforcing fetch/parse separation, station filter configs for all 3 vendors matching v1 PHP, and dietary tag normalization**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-08T00:56:50Z
- **Completed:** 2026-02-08T01:02:00Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- Installable Python project with all dependencies (httpx, selectolax, sqlmodel, asyncpg, pydantic-settings)
- Menu SQLModel table with JSONB stations_json column and unique constraint on (hall_id, date, meal)
- BaseParser abstract class with fetch_raw/parse separation, structural validation, and httpx error handling
- Station filter configs for Sodexo (12 hidden, 42 ordered), Bon Appetit (11 hidden, 23 ordered), Pomona (0 hidden, 14 ordered) matching v1 PHP exactly
- Dietary tag normalization covering Sodexo boolean fields, BAMCO cor_icon values, and Pomona dietaryChoices
- Sodexo station name normalization for SCR suffix, ALL CAPS, and blank/dash names

## Task Commits

Each task was committed atomically:

1. **Task 1: Project setup, config, and SQLModel data models** - `d1ec4a0` (feat)
2. **Task 2: Parser base class, station filters, and dietary tag normalization** - `69b747f` (feat)

## Files Created/Modified
- `backend/pyproject.toml` - Project metadata with all dependencies
- `backend/requirements.txt` - Pip-installable dependency list
- `backend/app/__init__.py` - App package init
- `backend/app/config.py` - Settings via pydantic-settings with database_url and timezone
- `backend/app/db.py` - Async SQLAlchemy engine, session factory, init_db
- `backend/app/models/__init__.py` - Re-exports all models
- `backend/app/models/enums.py` - MealPeriod, College, VendorType, DietaryTag enums
- `backend/app/models/dining_hall.py` - DiningHall SQLModel table
- `backend/app/models/menu.py` - Menu SQLModel table + ParsedMenu/ParsedMeal/ParsedStation/ParsedMenuItem Pydantic models
- `backend/app/parsers/__init__.py` - Re-exports BaseParser and filter configs
- `backend/app/parsers/base.py` - BaseParser ABC with fetch_raw/parse separation
- `backend/app/parsers/station_filters.py` - StationFilterConfig, apply_station_filters, 3 vendor configs, dietary tag normalization, Sodexo name normalization
- `backend/alembic.ini` - Alembic configuration for async PostgreSQL
- `backend/alembic/env.py` - Async migration runner with SQLModel metadata
- `backend/alembic/versions/.gitkeep` - Placeholder for migration versions
- `backend/tests/__init__.py` - Tests package init
- `backend/tests/conftest.py` - Pytest fixtures with sample menu factories

## Decisions Made
- Used `import datetime as _dt` aliasing in menu.py to avoid Pydantic 2.12 field name clash -- the `date` field name shadows the `date` type, which causes `PydanticUserError` when `UniqueConstraint` references it
- Typed `stations_json` as `Any` with `sa_column=Column(JSON)` and `default=None` for SQLModel 0.0.32 / Pydantic 2.12 compatibility (using `str` type annotation with `sa_column` causes build errors)
- Used `enum.Enum` (not `StrEnum`) with lowercase string values for database storage as specified
- Station filter pipeline preserves insertion order during merge using ordered dict keys

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed setuptools build backend path**
- **Found during:** Task 1 (pip install)
- **Issue:** `setuptools.backends._legacy:_Backend` does not exist in installed setuptools version
- **Fix:** Changed to standard `setuptools.build_meta`
- **Files modified:** backend/pyproject.toml
- **Verification:** `pip install -e ".[dev]"` succeeds
- **Committed in:** d1ec4a0 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed Pydantic field name clash with date type**
- **Found during:** Task 1 (model import verification)
- **Issue:** Field named `date` with type annotation `date` (from `datetime` import) clashes in Pydantic 2.12 when `UniqueConstraint` references the same column name, causing `PydanticUserError: unevaluable-type-annotation`
- **Fix:** Changed to `import datetime as _dt` and used `_dt.date` / `_dt.datetime` for type annotations in Menu model
- **Files modified:** backend/app/models/menu.py
- **Verification:** All model imports succeed
- **Committed in:** d1ec4a0 (Task 1 commit)

**3. [Rule 1 - Bug] Fixed SQLModel sa_column with JSON type annotation**
- **Found during:** Task 1 (model import verification)
- **Issue:** `stations_json: str = Field(sa_column=Column(JSON))` fails in SQLModel 0.0.32 / Pydantic 2.12 -- the `str` type conflicts with the JSON column type
- **Fix:** Changed to `Any` type with `default=None` alongside `sa_column=Column(JSON, nullable=False)`
- **Files modified:** backend/app/models/menu.py
- **Verification:** Menu model imports and metadata generated correctly
- **Committed in:** d1ec4a0 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correct operation with current library versions. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All shared foundations in place for parser implementations (Plans 02-04)
- BaseParser ABC ready for SodexoParser, BonAppetitParser, PomonaParser subclasses
- Station filter configs ready to be consumed by each parser's parse() method
- ParsedMenu/ParsedStation/ParsedMenuItem models ready as parser return types
- Dietary tag normalization ready to map vendor-specific labels in each parser
- Test conftest fixtures ready for parser test files

## Self-Check: PASSED

- All 5 key files verified on disk
- 2 commits found matching "01-01" pattern (d1ec4a0, 69b747f)

---
*Phase: 01-parsers-data-models*
*Completed: 2026-02-07*
