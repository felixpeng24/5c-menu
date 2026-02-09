# Roadmap: 5C Menu

## Overview

This roadmap delivers a complete dining hall menu app for the Claremont Colleges, progressing from data acquisition (parsers) through API infrastructure, user-facing web interface, and finally admin tooling. The critical path starts with parsers -- the entire app is useless without working scrapers -- then layers API caching and endpoints, the student-facing frontend, and lastly the admin panel for operational management.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Parsers & Data Models** - Scrape menus from all 3 vendors, persist to PostgreSQL, with validation and fallback
- [ ] **Phase 2: API & Caching** - Serve menu data via FastAPI endpoints with Redis caching and stampede prevention
- [ ] **Phase 3: Web Frontend** - Student-facing Next.js app with menu browsing, filtering, and responsive design
- [ ] **Phase 4: Admin Panel** - Magic link auth, hours management, and parser health monitoring

## Phase Details

### Phase 1: Parsers & Data Models
**Goal**: The system can fetch, validate, and persist daily menus from all 7 dining halls across 3 vendors
**Depends on**: Nothing (first phase)
**Requirements**: PARS-01, PARS-02, PARS-03, PARS-04, PARS-05, PARS-06, PARS-07, TEST-01
**Success Criteria** (what must be TRUE):
  1. Running the Sodexo parser returns structured menu data for Hoch-Shanahan with station groupings and dietary tags
  2. Running the Bon Appetit parser returns structured menu data for Collins, Malott, and McConnell with station groupings and dietary tags
  3. Running the Pomona parser returns structured menu data for Frank, Frary, and Oldenborg with station groupings and dietary tags
  4. When a parser fails (network error, HTML structure change), the system falls back to the last-known-good data stored in PostgreSQL
  5. Parser unit tests pass against saved HTML fixture snapshots for each vendor, validating extraction logic without network calls
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md -- Foundation: project setup, SQLModel models, parser base class, station filter configs
- [x] 01-02-PLAN.md -- Sodexo parser (Hoch-Shanahan) with fixture tests
- [x] 01-03-PLAN.md -- Bon Appetit parser (Collins, Malott, McConnell) with fixture tests
- [x] 01-04-PLAN.md -- Pomona parser (Frank, Frary, Oldenborg) + fallback orchestrator with fixture tests

### Phase 2: API & Caching
**Goal**: Menu data is served through fast, resilient API endpoints with intelligent caching
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05, TEST-02
**Success Criteria** (what must be TRUE):
  1. GET /api/v2/halls returns metadata for all 7 dining halls
  2. GET /api/v2/menus returns the menu for a specific hall, date, and meal period
  3. GET /api/v2/open-now returns only the halls currently serving a meal
  4. Repeated menu requests within 30 minutes are served from Redis cache (sub-100ms response), not by re-running parsers
  5. API integration tests pass covering all endpoints with expected response shapes
**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md -- App scaffold: FastAPI + Redis lifecycle, DiningHours model, response schemas, halls endpoint
- [ ] 02-02-PLAN.md -- Cache layer + request coalescing + menu service + menus endpoint
- [ ] 02-03-PLAN.md -- Hours service + open-now endpoint
- [ ] 02-04-PLAN.md -- Integration tests for all three endpoints

### Phase 3: Web Frontend
**Goal**: Students can browse dining hall menus, see what is open, and decide where to eat
**Depends on**: Phase 2
**Requirements**: FE-01, FE-02, FE-03, FE-04, FE-05, FE-06, FE-07, FE-08, FE-09, FE-10, FE-11, FE-12, TEST-03
**Success Criteria** (what must be TRUE):
  1. User sees all 7 dining halls in a vertical scroll feed with school color card backgrounds and open/closed badges
  2. User can tap meal tabs (Breakfast/Lunch/Dinner) on any hall card and see menu items grouped by station with dietary icons
  3. User can toggle "What's Open Now" to filter the feed to only halls currently serving a meal
  4. User can navigate to any date within the next 7 days via a date bar and see that day's menus
  5. User can use the app on a 375px mobile screen in both light and dark mode with no layout breakage
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Admin Panel
**Goal**: A single admin can manage dining hours, holiday overrides, and monitor parser health
**Depends on**: Phase 2
**Requirements**: ADM-01, ADM-02, ADM-03, ADM-04
**Success Criteria** (what must be TRUE):
  1. Admin receives a magic link email and can log in without a password
  2. Admin can view and edit dining hours in a halls-by-days grid, and changes are reflected in the open/closed status on the student-facing app
  3. Admin can create date-specific overrides (e.g., "Thanksgiving break: all halls closed") that supersede regular hours
  4. Admin can view a parser health dashboard showing last successful fetch time and error rates for each parser
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4
Note: Phase 3 and Phase 4 both depend on Phase 2 and could execute in parallel.

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Parsers & Data Models | 4/4 | Complete ✓ | 2026-02-07 |
| 2. API & Caching | 0/4 | Not started | - |
| 3. Web Frontend | 0/TBD | Not started | - |
| 4. Admin Panel | 0/TBD | Not started | - |
