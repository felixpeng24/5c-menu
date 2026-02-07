# Project Research Summary

**Project:** 5C Menu v2 — Claremont Colleges Dining App
**Domain:** College dining menu aggregation with web scraping, caching, and real-time crowding
**Researched:** 2026-02-07
**Confidence:** HIGH

## Executive Summary

The 5C Menu v2 is a college dining menu app serving the Claremont Colleges consortium (7 dining halls across 5 colleges, 3 different food service vendors). The recommended approach is a FastAPI backend with async web scrapers feeding a Redis cache layer (30-min TTL) backed by PostgreSQL persistence, fronted by a Next.js 15 web app on Vercel. The architecture follows a cache-aside pattern with stale-while-revalidate and PostgreSQL fallback to ensure resilience when vendor websites change or become unavailable.

The critical path is parser development — 3 vendor-specific scrapers (Sodexo, Bon Appetit, Pomona) that must handle unpredictable HTML structure changes without notice. Research confirms this is the highest-risk component based on prior art from similar college dining projects. The parsers must include structural validation, fallback CSS selectors, and health monitoring from day one. Bon Appetit specifically requires special attention as their site embeds menu data in JavaScript objects rather than semantic HTML, demanding either regex-based JSON extraction or discovery of undocumented JSON API endpoints.

Key risks are parser brittleness (mitigated by validation + monitoring + PostgreSQL fallback), cache stampede during peak meal times (mitigated by request coalescing + TTL jitter), and GPS indoor accuracy for the Phase 4 crowding feature (mitigated by expanded geofences + schedule-based fallback). The stack is deliberately modern but production-proven: Python 3.13, FastAPI 0.128.x, SQLModel/SQLAlchemy 2.0, Next.js 15, React 19, Tailwind v4, with all dependencies verified against official sources. Railway hosts the backend, Vercel hosts the frontend.

## Key Findings

### Recommended Stack

**Backend:** Python 3.13 + FastAPI 0.128.x + SQLModel 0.0.32 (over SQLAlchemy 2.0.46) + Uvicorn 0.40.0 as ASGI server. PostgreSQL 16.x for persistent storage, Redis 7.x for caching and ephemeral data (crowding). Scrapers use httpx 0.28.x (async HTTP client) + selectolax 0.4.6 (fast HTML parser, 10x faster than BeautifulSoup) with BeautifulSoup4 4.14.x as fallback. Magic link admin auth via Resend 2.21.x + python-jose 3.3.x for JWT tokens. Testing with pytest 9.x + pytest-asyncio.

**Frontend:** Next.js 15.x (not 16 due to breaking changes, not 14 due to lack of React 19 support) + React 19 + TypeScript 5.7.x + Tailwind CSS v4 (stable as of Jan 2025, 5x faster builds) + TanStack Query 5.90.x for server state management. Node.js 22.x LTS runtime. Client-side rendering with React Query fetching from the API (no SSR for dynamic menu data).

**Dev tools:** uv (Python package manager, 10-100x faster than pip), pnpm 10.x (Node package manager), Ruff 0.15.x (Python linter/formatter), ESLint 9 + Prettier or Biome 2.3.x (JS/TS linting). Railway for backend hosting, Vercel for frontend, Docker multi-stage builds for deployment.

**Core technologies:**
- **FastAPI + SQLModel**: API framework with Pydantic v2 integration, minimal boilerplate, auto-generated OpenAPI docs
- **Redis**: Menu cache (30-min TTL), location pings (2-min TTL), crowding snapshots (60-sec TTL) — ephemeral data with automatic expiration
- **PostgreSQL**: Source of truth for halls, hours, menus — persistent fallback when parsers fail or cache is cold
- **httpx + selectolax**: Async HTTP scraping with CSS selectors 10x faster than BeautifulSoup — speed matters for on-demand parsing
- **Next.js 15 + TanStack Query**: Client-side rendering with intelligent caching, stale-while-revalidate, and automatic refetching

### Expected Features

Research analyzed competitive dining apps (menu.jojodmo.com, the original 5Cs Menu iOS app, UCSC Menu, Nutrislice, Dine On Campus) to identify table stakes vs. differentiators.

**Must have (table stakes):**
- Daily menus for all 7 halls with meal-period tabs (Breakfast/Lunch/Dinner) and station grouping
- Open/closed status with accurate dining hours display (top user complaint in competitor reviews is wrong hours)
- Admin panel for hours management with holiday/break overrides
- 7-day future date navigation
- Mobile-responsive design optimized for 375px-wide screens (90%+ of usage is mobile)
- Dark mode following system preference
- Stale data handling with "Last updated X ago" timestamps
- School-specific color coding (gold=HMC, red=CMC, teal=Scripps, blue=Pomona, orange=Pitzer)
- Fast load times under 2 seconds (Redis caching + minimal JS bundle)

**Should have (competitive advantage):**
- "What's Open Now" filter toggle (no 5C competitor has this; low effort, high impact)
- Cross-hall food search ("Where is chicken tikka masala today?") — UCSC Menu has this, no 5C app does
- Dietary/allergen icons on menu items (vegan, vegetarian, gluten-free, nuts, etc.) — data quality depends on vendor API exposure
- Dietary preference filter with localStorage persistence (no accounts needed)
- PWA installability with offline menu cache via service worker
- Parser health dashboard (admin only) showing last successful fetch and error rates

**Defer (v2+):**
- Native mobile app (Phase 3) — only after web app proves adoption
- Real-time occupancy/crowding (Phase 4) — GPS indoor accuracy is a significant challenge, needs schedule-based fallback
- Push notifications (Phase 3, native only) — high ongoing cost, low opt-in rates
- User accounts, food ratings, meal plan balance checking — all classified as anti-features for this anonymous, solo-dev-maintained app

### Architecture Approach

Three-layer FastAPI architecture: thin routers handle HTTP concerns, thick services contain business logic, models/parsers handle data access. The core pattern is cache-aside with persistent fallback: check Redis first (30-min TTL), on miss run parser and dual-write to PostgreSQL + Redis, on parser failure fall back to last-known-good PostgreSQL data. Parsers inherit from an abstract base class with vendor-specific implementations, tested against saved HTML fixtures to avoid network dependencies in CI.

The data flow for menu requests (hot path) is: Client → React Query → API → Redis cache hit (95%+ of requests) → Client. Cache miss triggers: API → Parser → PostgreSQL persist → Redis cache → Client. The first user after cache expiry pays the scrape latency (2-5 seconds); all subsequent users get <100ms cached responses. This avoids scheduled jobs while maintaining data freshness.

For Phase 4 crowding, location pings are stored as ephemeral Redis keys (2-min TTL, self-expiring). A background aggregation job runs every 30 seconds scanning active sessions, applying geofence matching (50m+ radius to account for GPS indoor inaccuracy), counting per hall, and writing crowding snapshots. Schedule-based estimates serve as fallback when real data is insufficient.

**Major components:**
1. **Parser abstraction layer** — Base class with vendor implementations (Sodexo, Bon Appetit, Pomona), each with fallback CSS selectors and structural validation
2. **Service layer** — MenuService orchestrates cache-check → parser → persist; CrowdingService handles aggregation; HallService manages metadata + open/closed logic
3. **Dual storage** — Redis for speed (cache, ephemeral data), PostgreSQL for durability (source of truth, fallback on parser failure)
4. **Admin panel** — Magic link auth (Resend email), hours CRUD with override management, parser health dashboard
5. **React Query frontend** — Client-side rendering with intelligent caching, no SSR for dynamic menu data to avoid coupling Vercel deployment to Railway backend availability

### Critical Pitfalls

Research drew from prior art (broken RPI Sodexo scraper, Reed College Bon Appetit API shutdown, Carleton regex-based parser) and production patterns.

1. **Synchronous scraping on cache miss blocks API responses** — Cache miss runs parser before returning (2-30 sec latency). Multiple concurrent requests trigger duplicate scrapes (cache stampede). **Avoid with:** stale-while-revalidate pattern, request coalescing via Redis mutex locks, TTL jitter (25-35 min randomized), dual-write to PostgreSQL as fallback. Must be addressed in Phase 1.

2. **Parser brittleness without structural change detection** — Vendor sites redesign 1-2 times per academic year. CSS selectors break silently, returning empty menus. **Avoid with:** structural validation on every parse (minimum station count, required fields), parser health dashboard tracking last_successful_parse_at, fallback CSS selector chains (2-3 alternatives per data point), fixture versioning with dates, scheduled canary scrapes. Critical for Phase 1.

3. **Bon Appetit JavaScript-embedded data extraction** — BAMCO (serving Collins, Malott, McConnell — 3 of 7 halls) embeds menu data in `Bamco.menu_items` JavaScript objects, not semantic HTML. BeautifulSoup returns empty results. **Avoid with:** Before building, inspect Network tab for undocumented JSON API endpoints (e.g., `cafebonappetit.com/api/2/menus`). If no API, use regex on inline JS with aggressive validation. Do not default to headless browsers for a 30-min cache-miss path. Blocker for Phase 1.

4. **Cache stampede on TTL expiry during peak meal times** — At 12pm, hundreds of students open the app. Expired cache triggers 7 simultaneous scrapes. Vendor site rate-limits or blocks. **Avoid with:** Redis mutex lock per cache key (SETNX), probabilistic early expiration, TTL jitter, background refresh at 80% TTL, stale-while-revalidate. Must be addressed in Phase 1.

5. **GPS indoor accuracy destroys crowding feature credibility** — GPS accuracy degrades to 20-50m indoors. 50m geofence radius is barely larger than error margin. Frank and Frary are 50m apart with overlapping geofences. **Avoid with:** Increase geofence radius to 75-100m, filter pings with accuracy >50m, require 60+ sec dwell time, ship crowding as beta with clear expectations, plan for schedule-based fallback from day one. Phase 4 concern but fallback UI design starts in Phase 1.

6. **Cold start / chicken-and-egg problem for crowding data** — Zero users on launch day means zero location data. Crowding shows "Estimated" for all halls, no value, no adoption. **Avoid with:** Schedule-based estimates from day one, relax "contribute to see" rule initially, launch during Welcome Week (highest student density), gamify early adoption, target single busiest hall first. Phase 4 launch strategy.

## Implications for Roadmap

Based on combined research, the recommended phase structure reflects hard dependencies from architecture patterns, feature groupings from table-stakes analysis, and critical-path risks from pitfalls.

### Phase 1: Core Backend + API Foundation
**Rationale:** Parsers are the critical path and highest risk. The entire app is useless without working scrapers. Must build parser infrastructure (base class, validation, monitoring) before any frontend work can use real data. Cache architecture (stampede prevention, fallback logic) must be solved before any user load.

**Delivers:**
- SQLModel models for halls, hours, menus
- All 3 parsers (Sodexo, Bon Appetit, Pomona) with fallback selectors and structural validation
- MenuService with cache-aside + stale-while-revalidate + PostgreSQL fallback
- HallService with open/closed logic
- FastAPI routers: GET /halls, GET /menus, GET /open-now
- Parser health dashboard (admin-visible)

**Addresses features:**
- Daily menus for all 7 halls (table stakes)
- Meal-period organization (table stakes)
- Station grouping (table stakes)
- Stale data handling with timestamps (table stakes)

**Avoids pitfalls:**
- Pitfall 1 (synchronous scraping) — stale-while-revalidate implemented from day one
- Pitfall 2 (parser brittleness) — validation + monitoring + fallback selectors built into parser base class
- Pitfall 3 (Bon Appetit JS extraction) — Bon Appetit parser tested against live site, JSON API discovery prioritized
- Pitfall 4 (cache stampede) — Redis mutex locks + TTL jitter + request coalescing

**Research flag:** Standard FastAPI + scraper patterns. Skip `/gsd:research-phase` unless Bon Appetit JSON API discovery proves complex.

---

### Phase 2: Web Frontend + Core User Features
**Rationale:** Now that API returns real data, build the primary user-facing interface. Grouped together: hall list, menu display, date navigation, dark mode, open-now filter. All rely on Phase 1 API being stable.

**Delivers:**
- Next.js 15 App Router structure with Tailwind v4
- React Query hooks (useHalls, useMenu, useCrowding)
- Hall list page with "What's Open Now" filter
- Hall detail page with meal tabs, station grouping
- 7-day date navigation component
- Dark mode with school color cards (WCAG AA contrast-checked)
- Mobile-responsive layout (375px tested)

**Addresses features:**
- Mobile-responsive design (table stakes)
- Open/closed status per hall (table stakes) — consumes API from Phase 1
- Dining hall hours display (table stakes)
- "What's Open Now" filter (differentiator — low-effort competitive advantage)
- School color backgrounds (table stakes)
- Dark mode (table stakes)
- 7-day date navigation (table stakes)

**Avoids pitfalls:**
- UX pitfall: no empty states when parser fails (uses PostgreSQL fallback data with timestamp)
- UX pitfall: school colors unreadable in dark mode (WCAG AA contrast verification)
- UX pitfall: date boundaries use Pacific Time explicitly (no UTC drift)

**Research flag:** Standard Next.js + React Query patterns. Skip research.

---

### Phase 3: Admin Panel
**Rationale:** Hours management and parser monitoring are operational necessities but not user-facing. Can be built after core user experience ships. Requires same API + auth layer.

**Delivers:**
- Magic link auth via Resend (email-based, no password storage)
- JWT token generation and validation middleware
- Admin router with hours CRUD, override management
- Hours editor grid UI with date override system
- Parser health dashboard UI (extends backend metrics from Phase 1)

**Addresses features:**
- Admin panel with hours management (table stakes — enables accurate open/closed status)
- Parser health dashboard (already partially built in Phase 1, now adds UI)

**Avoids pitfalls:**
- Admin hours conflicts (validation prevents overlapping overrides)
- Security pitfall: magic link tokens have 10-min expiry + single-use invalidation

**Research flag:** Magic link auth is well-documented pattern (Resend has official guides). Skip research.

---

### Phase 4: Enhanced Discovery Features
**Rationale:** Once core menu browsing is proven stable, add features that improve discoverability and utility. Cross-hall search and dietary filtering both depend on menu data quality being validated through Phase 1-2 usage.

**Delivers:**
- Cross-hall food search with client-side indexing
- Dietary/allergen icon extraction per parser (vendor-dependent)
- Dietary preference filter with localStorage persistence
- PWA manifest + service worker
- Offline menu cache (today + tomorrow)

**Addresses features:**
- Cross-hall food search (differentiator — no 5C competitor has this)
- Dietary/allergen icons (differentiator)
- Dietary preference filter (differentiator)
- PWA installability (differentiator — removes App Store friction)
- Offline cache (differentiator — works in dead zones)

**Avoids pitfalls:**
- Performance trap: search indexes only today + tomorrow, not full 7-day cache
- UX pitfall: dietary icons clearly labeled as "from vendor," no health claims

**Research flag:** Dietary data extraction requires investigating each vendor's API/HTML structure. Consider `/gsd:research-phase` for dietary data discovery.

---

### Phase 5: Real-Time Crowding (High Risk)
**Rationale:** Crowding is the most technically complex and highest-risk feature. Requires mobile app development, location permissions, GPS accuracy handling, and cold-start adoption strategy. Defer until product-market fit proven through Phases 1-3.

**Delivers:**
- Location ping endpoint (POST /location) writing to Redis
- Aggregation job scanning Redis every 30 sec, applying geofence matching
- Crowding service with schedule-based fallback estimates
- GET /crowding endpoint returning per-hall levels
- React Native mobile app with expo-location integration (or web-based geolocation API as first iteration)

**Addresses features:**
- Real-time occupancy (deferred feature, high user value but high risk)

**Avoids pitfalls:**
- Pitfall 5 (GPS indoor accuracy) — 75-100m geofences, accuracy filtering, dwell time requirements, beta label
- Pitfall 6 (cold start) — schedule-based estimates from day one, no "contribute to see" barrier initially
- Security pitfall: coordinate validation against Claremont bounding box, per-IP rate limiting

**Research flag:** HIGH. GPS geofencing accuracy, Redis geospatial indexes, mobile location permissions, and cold-start adoption strategies all need deeper research. Run `/gsd:research-phase` before starting this phase.

---

### Phase Ordering Rationale

- **Parsers first (Phase 1):** Everything depends on working scrapers. Building frontend without real API data leads to mock-data drift.
- **Backend before frontend (Phases 1 → 2):** Frontend needs a stable API. Testing API endpoints with real parsers prevents surprises.
- **Admin after user features (Phase 3):** Hours management is operational infrastructure, not user-facing. User features prove adoption first.
- **Enhanced discovery after core stability (Phase 4):** Search and dietary filtering add value once menu data quality is validated through real usage.
- **Crowding last (Phase 5):** Most complex feature, requires mobile app, highest technical risk (GPS accuracy), needs proven user base for cold-start adoption.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 5 (Crowding):** GPS geofencing accuracy validation, Redis geospatial indexes vs SCAN-based aggregation trade-offs, mobile location permission UX patterns, cold-start adoption strategies for location-based features. Run `/gsd:research-phase` before implementation.
- **Phase 4 (Dietary data):** Each vendor exposes dietary info differently (or not at all). Needs per-vendor API/HTML inspection to determine feasibility. Consider `/gsd:research-phase` if dietary extraction proves complex during Phase 1 parser development.

**Phases with standard patterns (skip research):**
- **Phase 1 (Core Backend):** FastAPI + SQLModel + Redis cache-aside is well-documented. Parser patterns established. Only exception: if Bon Appetit JSON API discovery becomes blocked, may need brief research spike.
- **Phase 2 (Web Frontend):** Next.js 15 + React Query is extremely well-documented. Standard patterns apply.
- **Phase 3 (Admin Panel):** Magic link auth via Resend has official guides. CRUD patterns are standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI/npm/official docs. Python 3.13, FastAPI 0.128.x, Next.js 15, Tailwind v4, TanStack Query 5.x all confirmed stable and compatible. |
| Features | HIGH | Feature analysis drew from 6+ competitive apps (menu.jojodmo.com, 5Cs Menu iOS, UCSC Menu, Nutrislice, Dine On Campus, Campus Dining App). Table stakes vs differentiators clearly identified. |
| Architecture | HIGH | Patterns validated through FastAPI official docs, multiple production case studies (zhanymkanov best practices, Vinta monorepo, LSST vertical architecture), and prior art from similar college dining scrapers. Cache-aside + fallback is established pattern. |
| Pitfalls | MEDIUM-HIGH | Pitfalls verified through multiple sources: broken parser examples (RPI, Reed, Carleton), cache stampede literature (OneUptime, SlakNoah), GPS accuracy research (AttendanceRadar, geofencing systems). Prior 5C projects (5CMenu, 5cmenu by ccorcos) confirm domain-specific risks. Lower confidence on GPS crowding accuracy due to lack of 5C-specific field data. |

**Overall confidence:** HIGH

Research is comprehensive for Phases 1-4. Phase 5 (crowding) has identified risks but will need field testing to validate GPS accuracy assumptions.

### Gaps to Address

- **Bon Appetit JSON API availability:** BeautifulSoup-based parsing of BAMCO sites may fail if data is JavaScript-embedded. **Resolution:** During Phase 1 parser development, inspect Network tab for undocumented JSON API endpoints (e.g., `/api/2/menus?cafe={id}&date={date}`). If no API found, implement regex-based `Bamco.menu_items` extraction with aggressive validation. Budget 2-3 days for this investigation.

- **Dietary data vendor coverage:** Sodexo and Bon Appetit likely expose dietary info; Pomona source unknown. **Resolution:** During Phase 1 parser development, document what dietary metadata each vendor provides. If Pomona lacks dietary data, Phase 4 dietary filtering will be incomplete for Pomona halls (Frank, Frary, Oldenborg). Communicate this limitation clearly in UI.

- **GPS indoor accuracy field validation:** Research suggests 20-50m error indoors, but no Claremont-specific data. **Resolution:** Phase 5 should include 1-week field testing before public launch. Walk through each dining hall during meal times, log GPS accuracy values, measure actual geofence capture rate. If <60% capture rate, pivot to schedule-based estimates + self-reported crowding.

- **Railway free tier limits:** Research confirms Railway free tier exists but exact limits (CPU, memory, connection pooling) not verified. **Resolution:** During Phase 1 deployment, monitor Railway dashboard for resource usage. Budget for paid tier ($5-20/month) if free tier proves insufficient. PostgreSQL connection pooling (asyncpg + SQLAlchemy pool) must be configured to respect Railway connection limits.

## Sources

### Primary (HIGH confidence)
- FastAPI Official Documentation (routers, dependency injection, bigger applications)
- TanStack Query Official Documentation (React Query with Next.js App Router)
- SQLModel Official Documentation (SQLAlchemy 2.0 integration, async patterns)
- Next.js Official Blog (version 15 and 16 status, breaking changes)
- Tailwind CSS v4 Official Blog (stable release, migration guide)
- PyPI verified versions: fastapi 0.128.2, sqlmodel 0.0.32, uvicorn 0.40.0, redis-py 7.1.0, httpx 0.28.1, selectolax 0.4.6, pytest 9.0.2
- npm verified versions: @tanstack/react-query 5.90.x, next 15.x, pnpm 10.28.x

### Secondary (MEDIUM confidence)
- [FastAPI Best Practices (zhanymkanov GitHub)](https://github.com/zhanymkanov/fastapi-best-practices) — project structure, layered architecture
- [Building Scalable FastAPI with SQLModel (Medium)](https://medium.com/@faizulkhan56/building-a-scalable-fastapi-application-with-sqlmodel) — three-layer architecture
- [What is a Cache Stampede? (SlakNoah)](https://www.slaknoah.com/blog/what-is-a-cache-stampede-how-to-prevent-it-using-redis) — stampede prevention patterns
- [Redis Cache Stampede Prevention (OneUptime 2026)](https://oneuptime.com/blog/post/2026-01-30-cache-stampede-prevention/view) — single-flight pattern
- [Campus App Adoption Strategies (raftr 2025)](https://www.raftr.com/campus-app-adoption-strategies-for-2025/) — cold start
- [Geofencing Attendance Systems (AttendanceRadar)](https://attendanceradar.com/geofencing-attendance-systems-what-you-should-know/) — GPS spoofing, accuracy, indoor limitations

### Tertiary (LOW confidence, validation needed)
- [RPI Sodexo Menu Scraper (GitHub)](https://github.com/JelloRanger/menu-scraper) — parser brittleness example
- [Reed College Bon Appetit Menu App (GitHub)](https://github.com/Merlin04/reed-commons-menu) — API shutdown, forced HTML scraping
- [Carleton Bon Appetit Scraper (GitHub)](https://github.com/Machyne/pal/blob/master/api/bonapp/bon_api.py) — regex-based Bamco.menu_items extraction
- [5CMenu (annechristy GitHub)](https://github.com/annechristy/5CMenu) — prior 5C dining app
- [5cmenu (ccorcos GitHub)](https://github.com/ccorcos/5cmenu) — prior 5C dining app
- [CampusDish API (GitHub)](https://github.com/stevenleeg/campusdish_api) — college dining scraper architecture reference

---
*Research completed: 2026-02-07*
*Ready for roadmap: yes*
