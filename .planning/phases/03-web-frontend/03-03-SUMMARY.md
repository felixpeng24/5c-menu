---
phase: 03-web-frontend
plan: 03
subsystem: ui
tags: [react, tailwind, date-navigation, timezone, intl-api, dark-mode]

# Dependency graph
requires:
  - phase: 03-web-frontend
    plan: 01
    provides: "Next.js scaffold, Tailwind v4 theme, TypeScript types (MenuResponse.is_stale, fetched_at)"
provides:
  - "DateBar: 7-day Pacific-aware date navigation component"
  - "OpenNowToggle: pill-style toggle for filtering open halls"
  - "StaleBanner: amber relative-time stale data indicator"
  - "no-scrollbar CSS utility for hidden horizontal scroll"
affects: [03-04, 03-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [pacific-timezone-date-computation, intl-relative-time-format, dark-mode-inverted-selection]

key-files:
  created:
    - web/src/components/date-bar.tsx
    - web/src/components/open-now-toggle.tsx
    - web/src/components/stale-banner.tsx
  modified:
    - web/src/app/globals.css

key-decisions:
  - "Pacific timezone for today via toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' })"
  - "Intl.RelativeTimeFormat for stale banner (no date-fns dependency)"
  - "Pill toggle with dot indicator for OpenNowToggle (not native checkbox)"

patterns-established:
  - "Components in web/src/components/ with 'use client' directive"
  - "Pacific timezone awareness: all date computations use America/Los_Angeles"
  - "Dark mode: inverted selected states (bg-gray-900/dark:bg-white) for high contrast"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 3 Plan 3: Navigation and Filter Components Summary

**DateBar with Pacific timezone 7-day navigation, OpenNowToggle pill switch, and StaleBanner with Intl.RelativeTimeFormat**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T09:05:31Z
- **Completed:** 2026-02-09T09:07:07Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- DateBar renders 7 days starting from Pacific today with Today/Tomorrow labels and dark mode highlight
- OpenNowToggle provides pill-style active/inactive toggle with green dot indicator
- StaleBanner uses native Intl.RelativeTimeFormat for zero-dependency relative time display
- no-scrollbar CSS utility hides scrollbar on horizontal date navigation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create DateBar component with Pacific timezone support** - `65d7345` (feat)
2. **Task 2: Create OpenNowToggle and StaleBanner components** - `705225b` (feat)

## Files Created/Modified
- `web/src/components/date-bar.tsx` - 7-day date navigation with Pacific timezone awareness
- `web/src/components/open-now-toggle.tsx` - Pill toggle for "Open Now" filtering with dot indicator
- `web/src/components/stale-banner.tsx` - Amber stale data banner with Intl.RelativeTimeFormat
- `web/src/app/globals.css` - Added no-scrollbar utility classes for horizontal scroll

## Decisions Made
- Used `toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' })` for Pacific today -- this gives YYYY-MM-DD format directly without manual formatting
- Used `Intl.RelativeTimeFormat` instead of date-fns for the stale banner -- avoids adding a dependency for a single use case, well-supported in all modern browsers
- Styled OpenNowToggle as a pill button with dot indicator rather than native checkbox -- consistent with mobile-first design

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three navigation/filter components ready for composition in page.tsx (Plan 04)
- DateBar provides onDateChange callback for page-level date state management
- OpenNowToggle provides onToggle callback for open-now filtering
- StaleBanner consumes MenuResponse.is_stale and fetched_at directly

## Self-Check: PASSED

All 4 key files verified present. Both task commits (65d7345, 705225b) confirmed in git log. All three components export correctly (DateBar, OpenNowToggle, StaleBanner). no-scrollbar CSS utility confirmed in globals.css.

---
*Phase: 03-web-frontend*
*Completed: 2026-02-09*
