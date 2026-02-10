# 5C Menu

## What This Is

A dining hall menu app for the Claremont Colleges (5Cs) — a v2 rewrite of an existing PHP/MySQL/Swift app. Shows menus, hours, and open/closed status for all 7 dining halls across the 5 colleges. Built as a monorepo with a FastAPI backend, Next.js web frontend, and eventually a React Native mobile app.

## Core Value

Students can quickly see what's being served at every dining hall right now, so they can decide where to eat.

## Requirements

### Validated

- ✓ FastAPI backend serving RESTful API at /api/v2/ — v1.0
- ✓ 3 menu parsers (Sodexo, Bon Appetit, Pomona) via web scraping — v1.0
- ✓ All 7 dining halls supported from day one — v1.0
- ✓ PostgreSQL persistence + Redis caching (30-min TTL) — v1.0
- ✓ Next.js web frontend with menu display — v1.0
- ✓ Vertical scroll feed layout, meal tabs (Breakfast/Lunch/Dinner) — v1.0
- ✓ "What's Open Now" filter toggle — v1.0
- ✓ School color card backgrounds per hall (v1 hex codes) — v1.0
- ✓ 7-day date navigation (today + 6 days ahead) — v1.0
- ✓ Dark mode from day one (follow system default) — v1.0
- ✓ Mobile-first responsive design — v1.0
- ✓ Admin panel with hours table editor (halls × days grid) — v1.0
- ✓ Admin override management for holidays/breaks — v1.0
- ✓ Magic link admin auth via Resend (single hardcoded email) — v1.0
- ✓ Parser status dashboard in admin panel — v1.0
- ✓ Dietary tags parsed from vendor data — v1.0
- ✓ Parser failure UX: show stale data + "last updated" timestamp — v1.0
- ✓ Station filtering replicating v1 logic — v1.0
- ✓ Full test coverage: parsers (pytest + fixtures), API, key frontend components (Vitest) — v1.0

### Active

(None — next milestone not yet defined)

### Out of Scope

- Settings page — defer to later phase
- Mobile app (Expo/React Native) — future milestone
- Crowding/location features — future milestone
- Ads system — dropped entirely
- OAuth/social login — not needed, app is anonymous for users
- User accounts / authentication — app is anonymous; localStorage for preferences
- Food ratings / reviews — moderation nightmare for solo dev
- Meal plan balance checking — requires storing student credentials
- Mobile ordering / pre-ordering — requires POS integration
- Push notifications — high cost, low opt-in rates
- Nutrition calculator / calorie tracking — vendor data quality inconsistent
- Social features — students coordinate via existing apps
- Multi-language support — English-speaking campus
- Apple Watch / wearable support — tiny user base

## Context

Shipped v1.0 MVP with 6,663 LOC (Python + TypeScript + CSS).
Tech stack: FastAPI + SQLModel (backend), Next.js 15 + Tailwind v4 + TanStack Query (web).
Deployment targets: Railway (backend + Postgres + Redis), Vercel (web).
107 automated tests passing across all layers.

**v2 rewrite** of existing app at `../menu-backend` (PHP/MySQL backend + Swift iOS app).
**Solo developer** building and maintaining everything.
All 3 vendor parsers verified to require web scraping (no public APIs).
v1 codebase available as reference for station filtering rules, school colors, and parser logic.

## Constraints

- **Tech stack**: FastAPI + SQLModel (backend), Next.js 15 + Tailwind v4 (web), Expo (mobile later) — already decided
- **Deployment**: Railway (backend + Postgres + Redis), Vercel (web) — accounts already set up
- **Repo structure**: Monorepo with backend/, web/, mobile/ directories
- **API versioning**: /api/v2/ path prefix
- **Admin auth**: Magic link via Resend to single hardcoded admin email
- **Rendering**: Client-side (React Query fetches data, no SSR for dynamic menu content)
- **Data sources**: Web scraping only — no vendor APIs available

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLModel over SQLAlchemy | Less boilerplate, built for FastAPI | ✓ Good — worked well with Pydantic 2, minor aliasing needed for `date` field |
| Client-side rendering | React Query for dynamic data simpler than SSR | ✓ Good — TanStack Query handles caching/polling cleanly |
| Magic link auth (Resend) | Single admin, no password to manage | ✓ Good — simple flow, anti-enumeration pattern |
| Vertical scroll feed | All halls stacked vertically (not horizontal swipe like v1) | ✓ Good — works well on mobile |
| Meal tabs | Breakfast/Lunch/Dinner tabs per hall | ✓ Good — clean per-card interaction |
| School color backgrounds | Bold color card backgrounds like v1 | ✓ Good — college identity preserved |
| Fresh Python parsers | Don't port PHP, reverse-engineer vendor sites in Python | ✓ Good — cleaner code, httpx + selectolax |
| Monorepo | backend/, web/, mobile/ in one repo | ✓ Good — single repo simplifies development |
| Tailwind v4 CSS-first config | @theme in globals.css, no tailwind.config.ts | ✓ Good — simpler configuration |
| Redis lifespan management | FastAPI lifespan context manager, not module-level singleton | ✓ Good — clean startup/shutdown |
| Jittered cache TTL | 1800s +/- 300s to prevent thundering herd | ✓ Good — prevents synchronized cache expiration |
| Request coalescing | asyncio.Future for stampede prevention | ✓ Good — handles concurrent cache misses |
| Pacific timezone for "today" | America/Los_Angeles for date computation | ✓ Good — matches campus timezone |
| httpOnly session cookies | Secure cookie for admin sessions, not localStorage | ✓ Good — prevents XSS token theft |

---
*Last updated: 2026-02-10 after v1.0 milestone*
