---
phase: 03-web-frontend
plan: 01
subsystem: ui
tags: [next.js, tailwind-v4, tanstack-query, vitest, react, typescript]

# Dependency graph
requires:
  - phase: 02-api-caching
    provides: "REST API endpoints (halls, menus, open-now) that frontend fetches from"
provides:
  - "Next.js 15 app scaffold with App Router and src/ directory"
  - "TanStack Query v5 provider wrapping the app"
  - "API client (fetchHalls, fetchMenu, fetchOpenNow) with typed responses"
  - "Custom query hooks (useHalls, useMenu, useOpenNow)"
  - "Tailwind CSS v4 with @theme school colors"
  - "Vitest + Testing Library configured for component tests"
  - "TypeScript interfaces matching backend Pydantic schemas"
  - "Hall meal configs, dietary tag labels, college color map constants"
affects: [03-02, 03-03, 03-04, 03-05]

# Tech tracking
tech-stack:
  added: [next.js 15.5.12, react 19.1, tailwindcss 4, @tanstack/react-query 5, vitest 4, @testing-library/react 16, jsdom 28]
  patterns: [app-router, css-first-tailwind-config, use-client-query-provider, api-client-with-env-base-url]

key-files:
  created:
    - web/src/lib/types.ts
    - web/src/lib/api.ts
    - web/src/lib/constants.ts
    - web/src/lib/query-provider.tsx
    - web/src/lib/hooks.ts
    - web/vitest.config.mts
    - web/src/test-setup.ts
    - web/.env.example
  modified:
    - web/src/app/globals.css
    - web/src/app/layout.tsx
    - web/src/app/page.tsx
    - web/postcss.config.mjs
    - web/package.json

key-decisions:
  - "Tailwind v4 CSS-first config via @theme in globals.css (no tailwind.config.ts)"
  - "QueryProvider uses useState pattern to avoid recreating QueryClient on re-renders"
  - "useOpenNow polls every 60s; useHalls has 5min staleTime for rarely-changing metadata"
  - "postcss.config.mjs uses object syntax for @tailwindcss/postcss plugin"
  - "Fixed .gitignore to allow .env.example through .env* exclusion"

patterns-established:
  - "API client: centralized apiFetch<T> with NEXT_PUBLIC_API_URL env var"
  - "Query hooks: one per endpoint in web/src/lib/hooks.ts with 'use client' directive"
  - "Types: TypeScript interfaces in web/src/lib/types.ts matching backend schemas exactly"
  - "Constants: college colors, dietary icons, hall meals in web/src/lib/constants.ts"

# Metrics
duration: 4min
completed: 2026-02-09
---

# Phase 3 Plan 1: Next.js 15 Scaffold Summary

**Next.js 15 app with TanStack Query v5 hooks, Tailwind v4 school colors, typed API client, and Vitest test infrastructure**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-09T08:58:41Z
- **Completed:** 2026-02-09T09:02:55Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments
- Scaffolded Next.js 15.5.12 with App Router, TypeScript strict mode, and src/ directory
- Configured Tailwind CSS v4 with @theme school colors for all 5 Claremont colleges
- Created typed API client with fetchHalls, fetchMenu, fetchOpenNow matching backend schemas
- Built TanStack Query v5 provider and custom hooks with smart staleTime and polling
- Set up Vitest 4 with jsdom, React plugin, and Testing Library

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold Next.js 15 app and install all dependencies** - `96cae75` (feat)
2. **Task 2: Create API client, types, constants, query hooks, and QueryProvider** - `e172933` (feat)

## Files Created/Modified
- `web/package.json` - Next.js 15, TanStack Query, Vitest dependencies and test scripts
- `web/postcss.config.mjs` - Tailwind v4 PostCSS plugin (object syntax)
- `web/src/app/globals.css` - Tailwind v4 import + @theme school colors
- `web/src/app/layout.tsx` - Root layout wrapping children in QueryProvider
- `web/src/app/page.tsx` - Minimal placeholder page
- `web/src/lib/types.ts` - TypeScript interfaces matching backend Pydantic schemas
- `web/src/lib/api.ts` - Centralized API client with NEXT_PUBLIC_API_URL
- `web/src/lib/constants.ts` - College colors, dietary icons, hall meal configs
- `web/src/lib/query-provider.tsx` - Client-side QueryClientProvider wrapper
- `web/src/lib/hooks.ts` - useHalls, useMenu, useOpenNow query hooks
- `web/vitest.config.mts` - Vitest config with jsdom, React plugin, tsconfig paths
- `web/src/test-setup.ts` - Testing Library jest-dom matchers
- `web/.env.example` - NEXT_PUBLIC_API_URL template
- `web/.gitignore` - Fixed to allow .env.example

## Decisions Made
- Used Tailwind v4 CSS-first config (`@theme` in globals.css) instead of JS config file -- this is the v4 standard
- QueryProvider uses `useState(() => new QueryClient(...))` pattern to prevent re-creating the client on every render
- useOpenNow polls at 60s intervals for live dining hall status; useHalls uses 5-minute staleTime since hall metadata changes rarely
- Fixed scaffolded postcss.config.mjs from array syntax to object syntax for plugin compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed .gitignore to allow .env.example**
- **Found during:** Task 1 (staging files)
- **Issue:** Scaffolded `.gitignore` had `.env*` pattern which excluded `.env.example`
- **Fix:** Added `!.env.example` exception after `.env*` rule
- **Files modified:** `web/.gitignore`
- **Verification:** `git add web/.env.example` succeeded
- **Committed in:** 96cae75 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor gitignore fix required for committing .env.example. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All infrastructure in place for component development (Plan 02: hall cards, menu display)
- API client and hooks ready to be consumed by UI components
- Vitest configured and ready for component tests
- Tailwind school colors available as theme classes (bg-hmc, bg-cmc, etc.)

## Self-Check: PASSED

All 14 key files verified present. Both task commits (96cae75, e172933) confirmed in git log.

---
*Phase: 03-web-frontend*
*Completed: 2026-02-09*
