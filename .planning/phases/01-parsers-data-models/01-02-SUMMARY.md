---
phase: 01-parsers-data-models
plan: 02
subsystem: parsers
tags: [sodexo, parser, html-extraction, station-filtering, dietary-tags]
dependency_graph:
  requires: [01-01]
  provides: [SodexoParser, sodexo-fixture]
  affects: [01-03, 01-04, 02-01]
tech_stack:
  added: []
  patterns: [json-in-html-extraction, station-filter-pipeline, fixture-based-testing]
key_files:
  created:
    - backend/app/parsers/sodexo.py
    - backend/tests/test_sodexo_parser.py
    - backend/tests/fixtures/sodexo/hoch_2026-02-07.html
  modified:
    - backend/app/parsers/__init__.py
decisions: []
metrics:
  duration: 4 min
  completed: 2026-02-07
---

# Phase 1 Plan 2: Sodexo Parser Summary

SodexoParser extracts menu data from Sodexo JSON-in-HTML, applies station name normalization and the full filter pipeline (hide/truncate/order/merge), and extracts dietary tags from boolean fields -- validated by 33 fixture-based tests.

## What Was Built

### SodexoParser (`backend/app/parsers/sodexo.py`)

- Inherits `BaseParser` with `fetch_raw()` (async httpx) and `parse()` (pure, no I/O)
- `build_url(target_date)` formats Sodexo URL with `MM/DD/YYYY` startdate parameter
- JSON extraction from `#nutData` div via selectolax CSS selector (regex fallback)
- Sodexo returns a week of data; parser filters to the requested target_date
- Station name normalization: strips "SCR" suffix, title-cases ALL CAPS, fixes "And"/"To"/"HMC", blank/dash to "Miscellaneous"
- Merges items into stations with the same normalized name within each meal
- Skips empty Miscellaneous stations (matching v1 PHP behavior)
- Applies `apply_station_filters(SODEXO_FILTER)` pipeline: merge aliases, hide, truncate, sort, remove empty
- Dietary tags extracted from `isVegan`/`isVegetarian`/`isMindful` boolean fields, mapped through `DIETARY_TAG_MAP`

### Unit Tests (`backend/tests/test_sodexo_parser.py`)

33 tests organized in 10 test classes:
- **Structure**: ParsedMenu type, hall_id, date, meals present
- **Stations**: every meal has stations, every station has items, item names non-empty
- **Hidden filtering**: no hidden stations appear (salad bar, deli bar, hot cereal, etc.)
- **Ordering**: stations in v1-ordered relative order
- **Truncation**: Grill <= 3 items, Breakfast <= 12 items
- **Dietary tags**: tags present, all canonical, vegan and vegetarian confirmed
- **Name normalization**: SCR stripping, ucwords, blank/dash to Miscellaneous, mixed case preserved
- **Validation**: empty menu returns False, valid menu returns True
- **Combined merging**: stew+soup -> Soups, alias stations merge correctly
- **Date filtering**: wrong date returns empty, other dates in week work
- **URL building**: format correctness

### Fixture (`backend/tests/fixtures/sodexo/hoch_2026-02-07.html`)

- Live HTML captured from Sodexo for Hoch-Shanahan, week of 2026-02-01 to 2026-02-07
- Feb 7 is a Saturday: 2 meal periods (brunch, dinner), 13 raw station names, 97 items
- Contains vegan (45), vegetarian (75), and mindful (46) tagged items
- 5MB file with full nutritional data in the JSON payload

## Deviations from Plan

None -- plan executed exactly as written.

## Task Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | SodexoParser implementation + fixture | `8b42f23` |
| 2 | Unit tests (33 passing) | `cd90da2` |

## Verification Results

```
33 passed in 1.21s
```

All success criteria met:
- SodexoParser.parse() takes raw HTML and returns ParsedMenu with correct meals/stations/items
- Hidden stations (salad bar, deli bar, etc.) removed
- Stations sorted per v1 ORDERED_STATIONS list
- Grill truncated to 3 items, breakfast to 12
- Combined stations merged (stew+soup -> Soups)
- Dietary tags (vegan, vegetarian, mindful) extracted from Sodexo boolean fields
- All tests pass against saved fixture without network

## Self-Check: PASSED

- backend/app/parsers/sodexo.py: FOUND
- backend/tests/test_sodexo_parser.py: FOUND
- backend/tests/fixtures/sodexo/hoch_2026-02-07.html: FOUND
- Commit 8b42f23: FOUND
- Commit cd90da2: FOUND
