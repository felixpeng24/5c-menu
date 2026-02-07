# 5C Menu

## What This Is

A dining hall menu app for the Claremont Colleges (5Cs) — a v2 rewrite of an existing PHP/MySQL/Swift app. Shows menus, hours, and open/closed status for all 7 dining halls across the 5 colleges. Built as a monorepo with a FastAPI backend, Next.js web frontend, and eventually a React Native mobile app.

## Core Value

Students can quickly see what's being served at every dining hall right now, so they can decide where to eat.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] FastAPI backend serving RESTful API at /api/v2/
- [ ] 3 menu parsers (Sodexo, Bon Appetit, Pomona) via web scraping
- [ ] All 7 dining halls supported from day one
- [ ] PostgreSQL persistence + Redis caching (30-min TTL)
- [ ] Next.js web frontend with menu display
- [ ] Vertical scroll feed layout, meal tabs (Breakfast/Lunch/Dinner)
- [ ] "What's Open Now" filter toggle
- [ ] School color card backgrounds per hall (v1 hex codes)
- [ ] 7-day date navigation (today + 6 days ahead)
- [ ] Dark mode from day one (follow system default)
- [ ] Mobile-first responsive design
- [ ] Admin panel with hours table editor (halls × days grid)
- [ ] Admin override management for holidays/breaks
- [ ] Magic link admin auth via Resend (single hardcoded email)
- [ ] Parser status dashboard in admin panel
- [ ] Dietary tags parsed from vendor data
- [ ] Parser failure UX: show stale data + "last updated" timestamp
- [ ] Station filtering replicating v1 logic
- [ ] Full test coverage: parsers (pytest + fixtures), API, key frontend components (Vitest)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Settings page — defer to later phase
- Mobile app (Expo/React Native) — Phase 3
- Crowding/location features — Phase 4
- Ads system — dropped entirely from v1
- OAuth/social login — not needed, app is anonymous for users
- Real-time chat — not relevant to dining menu use case
- Video content — not relevant

## Context

- **v2 rewrite** of existing app at `../menu-backend` (PHP/MySQL backend + Swift iOS app)
- **Solo developer** building and maintaining everything
- **Timeline**: ASAP (weeks) for Phase 1
- All 3 vendor parsers verified to require web scraping (no public APIs)
- v1 codebase available as reference for station filtering rules, school colors, and parser logic
- Parsers: Sodexo (HMC Hoch-Shanahan), Bon Appetit (CMC Collins, Scripps Malott, Pitzer McConnell), Pomona (Frank, Frary, Oldenborg)
- Existing codebase mapped in `.planning/codebase/`

## Constraints

- **Tech stack**: FastAPI + SQLModel (backend), Next.js 14 + Tailwind (web), Expo (mobile later) — already decided
- **Deployment**: Railway (backend + Postgres + Redis), Vercel (web) — accounts already set up
- **Repo structure**: Monorepo with backend/, web/, mobile/ directories
- **API versioning**: /api/v2/ path prefix
- **Admin auth**: Magic link via Resend to single hardcoded admin email
- **Rendering**: Client-side (React Query fetches data, no SSR for dynamic menu content)
- **Data sources**: Web scraping only — no vendor APIs available

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLModel over SQLAlchemy | Less boilerplate, built for FastAPI | — Pending |
| Client-side rendering | React Query for dynamic data simpler than SSR | — Pending |
| Magic link auth (Resend) | Single admin, no password to manage | — Pending |
| Vertical scroll feed | All halls stacked vertically (not horizontal swipe like v1) | — Pending |
| Meal tabs | Breakfast/Lunch/Dinner tabs per hall | — Pending |
| School color backgrounds | Bold color card backgrounds like v1 | — Pending |
| Fresh Python parsers | Don't port PHP, reverse-engineer vendor sites in Python | — Pending |
| Monorepo | backend/, web/, mobile/ in one repo | — Pending |
| Phase 1 = merged PRD Phase 1+2 | Ship backend + web + admin together | — Pending |

---
*Last updated: 2026-02-07 after initialization*
