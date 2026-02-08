# Phase 1: Parsers & Data Models - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Fetch, validate, and persist daily menus from all 7 dining halls across 3 vendors (Sodexo, Bon Appétit, Pomona) into PostgreSQL. Includes SQLModel data models, parser base class with vendor implementations, structural validation, fallback to last-known-good data, and parser unit tests against HTML fixtures. Does NOT include API endpoints, caching layer, frontend, or admin panel — those are later phases.

</domain>

<decisions>
## Implementation Decisions

### Parser approach
- Write fresh Python parsers — do NOT port PHP code from v1
- Reference v1 PHP parsers for station filtering rules, ordering, and truncation logic, then reimplement in Python
- Use httpx for async HTTP requests + selectolax for fast HTML parsing (BeautifulSoup4 as fallback)
- Abstract base class with vendor-specific implementations (Sodexo, Bon Appétit, Pomona)

### Vendor mapping
- **Sodexo**: Hoch-Shanahan (HMC) — 1 hall
- **Bon Appétit**: Collins (CMC), Malott (Scripps), McConnell (Pitzer) — 3 halls
- **Pomona**: Frank, Frary, Oldenborg — 3 halls
- All 7 halls supported from day one

### Bon Appétit extraction strategy
- BAMCO embeds menu data in JavaScript objects (`Bamco.menu_items`), not semantic HTML
- First attempt: discover undocumented JSON API endpoints (e.g., `cafebonappetit.com/api/2/menus`)
- Fallback: regex-based extraction from inline JS with aggressive validation
- Do NOT use headless browsers — too slow for cache-miss path

### Data model
- SQLModel ORM (not raw SQLAlchemy) — less boilerplate, built for FastAPI
- PostgreSQL as persistent source of truth
- Menu items grouped by: hall → date → meal period → station → items
- Dietary tags stored per menu item, parsed from vendor data

### Station filtering
- Replicate v1 station filtering logic exactly
- Same station ordering and truncation rules as PHP parsers
- Reference v1 codebase at `../menu-backend` for exact rules

### Dietary tags
- Parse whatever dietary labels/icons each vendor provides (vegan, vegetarian, gluten-free, etc.)
- Normalize tag names across vendors to a consistent set
- If a vendor doesn't provide dietary data, store empty — don't fabricate

### Validation & fallback
- Structural validation on every parse: minimum station count, required fields present
- Fallback CSS selector chains (2-3 alternatives per data point) for parser resilience
- On parser failure (network error, HTML structure change), fall back to last-known-good data in PostgreSQL
- Parser failure UX downstream: stale data shown with "Last updated X ago" timestamp

### Testing
- pytest with saved HTML fixture snapshots for each vendor
- Test extraction logic without network calls
- Fixture files versioned with dates for tracking vendor site changes

### Claude's Discretion
- Exact SQLModel schema design (table structure, column types, relationships)
- Parser base class interface design
- Validation thresholds (e.g., minimum station count to consider valid)
- How to handle Oldenborg's fewer meal periods (it naturally has fewer — no special casing needed per user decision)
- Exact dietary tag normalization mapping
- Temp file and error logging approach

</decisions>

<specifics>
## Specific Ideas

- "Keep the general layout/feel [of v1], modernize with React/Tailwind" — this applies to frontend phases, but parser output should preserve the same data granularity v1 users expect
- Station filtering must match v1 behavior — users are familiar with the existing ordering
- Oldenborg should be treated the same as other halls, just shows fewer meals naturally
- v1 school color hex codes need to be extracted from v1 codebase (for later phases, but parser hall metadata should include school association)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. All API, caching, frontend, and admin decisions are documented in DECISIONS.md for their respective phases.

</deferred>

---

*Phase: 01-parsers-data-models*
*Context gathered: 2026-02-07*
