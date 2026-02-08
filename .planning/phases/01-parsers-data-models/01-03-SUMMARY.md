---
phase: 01-parsers-data-models
plan: 03
subsystem: parsers
tags: [bon-appetit, bamco, regex, parser, fixtures]
dependency-graph:
  requires: [01-01]
  provides: [BonAppetitParser, bonappetit-fixtures]
  affects: [api-endpoints, scheduler]
tech-stack:
  added: []
  patterns: [regex-js-extraction, special-field-filtering, cor_icon-dietary-tags]
key-files:
  created:
    - backend/app/parsers/bonappetit.py
    - backend/tests/test_bonappetit_parser.py
    - backend/tests/fixtures/bonappetit/collins_2026-02-07.html
    - backend/tests/fixtures/bonappetit/malott_2026-02-07.html
    - backend/tests/fixtures/bonappetit/mcconnell_2026-02-07.html
  modified: []
decisions:
  - BAMCO special field is integer (0/1), not boolean -- used truthiness check
  - "Seafood Watch" cor_icon value dropped (not in DIETARY_TAG_MAP) -- logged as warning
  - Station labels in dayparts use "@" prefix but not HTML tags; menu_items station field has HTML
  - Combined filter renames "grill" to "grill special", so truncation limit for "grill" does not apply post-combine
metrics:
  duration: 5 min
  completed: 2026-02-07
---

# Phase 1 Plan 3: Bon Appetit Parser Summary

Regex extraction of Bamco.menu_items and Bamco.dayparts from inline JavaScript for Collins (CMC), Malott (Scripps), and McConnell (Pitzer) with special-field filtering, cor_icon dietary tags, station filter pipeline, and 20 passing unit tests.

## What Was Built

### BonAppetitParser (`backend/app/parsers/bonappetit.py`)

Parser for 3 BAMCO dining halls that:

1. **Builds URLs** from hall config with date formatting (YYYY-MM-DD)
2. **Extracts Bamco.menu_items** via regex `Bamco\.menu_items\s*=\s*(\{[^;]+\});` -- JSON object keyed by item ID containing label, special field, cor_icon dietary tags, station info
3. **Extracts Bamco.dayparts** via regex `Bamco\.dayparts\['(\d+)'\]\s*=\s*(\{[^;]+\});` -- multiple assignments, each mapping a daypart ID to meal label + station list with item ID arrays
4. **Filters by special field** -- only items with `special` truthy (value=1) are included; items with `special=0` are excluded (327 out of 372 items in Collins fixture)
5. **Extracts dietary tags** from `cor_icon` dict values and normalizes via `normalize_dietary_tags()` -- handles Vegan, Vegetarian, Made without Gluten-Containing Ingredients, In Balance, Farm to Fork, Humane
6. **Cleans station labels** -- strips HTML tags via regex, removes leading "@" prefix, trims whitespace
7. **Deduplicates items** within each station by lowercased label (first occurrence kept)
8. **Applies station filter pipeline** via `apply_station_filters(stations, BONAPPETIT_FILTER)` -- hide, combine, truncate, order

Hall configuration:
- Collins: `https://collins-cmc.cafebonappetit.com/cafe/collins/{date}`
- Malott: `https://scripps.cafebonappetit.com/cafe/malott-dining-commons/{date}`
- McConnell: `https://pitzer.cafebonappetit.com/cafe/mcconnell-bistro/{date}`

### Fixtures

All 3 fixtures fetched from live BAMCO sites on 2026-02-07:
- Collins: 1.5 MB, 372 items (45 special), 2 dayparts (Brunch, Dinner)
- Malott: 1.2 MB, 260 items (46 special), 3 dayparts (Brunch, Lunch, Dinner)
- McConnell: 1.1 MB, 347 items (89 special), 2 dayparts (Brunch, Dinner)

### Unit Tests (`backend/tests/test_bonappetit_parser.py`)

20 tests in 8 test classes:
- **TestBamcoRegexExtraction** (3): basic parse, missing menu_items error, missing dayparts error
- **TestBamcoAllHalls** (2): all 3 halls parse successfully, invalid hall rejected
- **TestBamcoMealsAndStations** (1): meals have stations with named items
- **TestBamcoSpecialFiltering** (2): synthetic special=0 excluded, fixture non-special items excluded
- **TestBamcoStationFiltering** (3): hidden stations removed, ordering correct, truncation limits respected
- **TestBamcoDietaryTags** (2): tags from fixture are canonical, synthetic cor_icon produces correct tags
- **TestBamcoLabelCleaning** (2): HTML+@ stripping in parser, direct _clean_station_label tests
- **TestBamcoDuplicateItems** (1): duplicate labels deduplicated to first occurrence
- **TestBamcoTruncation** (2): fixture truncation verified, synthetic breakfast @home truncation
- **TestBamcoBuildUrl** (2): URL format correct, all halls produce valid URLs

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| # | Hash | Description |
|---|------|-------------|
| 1 | cd90da2 | feat(01-03): implement BonAppetitParser with regex extraction and save fixtures |
| 2 | 70b04aa | test(01-03): add Bon Appetit parser unit tests |

## Self-Check: PASSED

- All 5 key files verified on disk
- 2 commits found matching "01-03" in git log
- 20/20 tests pass
