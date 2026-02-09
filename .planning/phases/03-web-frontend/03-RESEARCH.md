# Phase 3: Web Frontend - Research

**Researched:** 2026-02-09
**Domain:** Next.js App Router + TanStack Query + Tailwind CSS v4 (client-side rendering)
**Confidence:** HIGH

## Summary

Phase 3 builds the student-facing web app inside the existing `web/` directory. The app is a client-side SPA that fetches data from 3 existing API endpoints (`/api/v2/halls`, `/api/v2/menus`, `/api/v2/open-now`) and renders a vertical scroll feed of dining hall cards with meal tabs, station groupings, dietary icons, and open/closed badges. Dark mode follows the system default via Tailwind's built-in `prefers-color-scheme` support.

The stack is Next.js 15 (App Router, LTS until Oct 2026) + TanStack Query v5 (async state management) + Tailwind CSS v4 (CSS-first configuration). All three are mature, well-documented, and compatible with each other as of Feb 2026. Vitest + React Testing Library handle component tests (TEST-03).

One notable gap: the current API does not expose dining hall hours (FE-07 requirement). The `/api/v2/halls` endpoint returns `{id, name, college, vendor_type, color}` without schedule data. Either the backend needs a new endpoint/field, or the frontend must work around this. This is the single cross-phase dependency to resolve.

**Primary recommendation:** Use `create-next-app` with Next.js 15 (pinned, not `@latest` which gives 16), Tailwind CSS v4 via `@tailwindcss/postcss`, TanStack Query v5 for data fetching, and Vitest for testing. Keep everything client-rendered -- no SSR, no server components for data.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 15.5.x (LTS) | App Router framework | LTS until Oct 2026; mature App Router; avoids Next.js 16 breaking changes (middleware-to-proxy, Turbopack-only) |
| React | 18.x (ships with Next.js 15) | UI library | Stable, proven; Next.js 16 requires React 19 which is less battle-tested |
| @tanstack/react-query | 5.x | Async state / data fetching | Official React Query; caching, refetching, stale-while-revalidate built in |
| Tailwind CSS | 4.x | Utility-first CSS | CSS-first config, 5x faster builds, native dark mode support |
| TypeScript | 5.x | Type safety | Ships with create-next-app; matches backend Pydantic schemas |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tailwindcss/postcss | 4.x | PostCSS plugin for Tailwind v4 | Required for Next.js integration (replaces old tailwindcss PostCSS plugin) |
| vite-tsconfig-paths | latest | Path alias resolution in Vitest | Resolves `@/` imports in test files |
| @vitejs/plugin-react | latest | JSX transform for Vitest | Required for Vitest to process React components |
| @testing-library/react | latest | Component test utilities | Render and query components in tests |
| @testing-library/jest-dom | latest | DOM assertion matchers | `toBeInTheDocument()`, `toHaveTextContent()`, etc. |
| jsdom | latest | DOM environment for Vitest | Simulates browser DOM in Node.js test runner |
| vitest | latest | Test runner | Fast, Vite-native; official Next.js recommendation for unit tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Next.js 15 | Next.js 16 (latest) | 16 has breaking changes (middleware renamed to proxy, Turbopack mandatory, React 19 required). For a pure client-side app with no SSR, 15 LTS is lower risk and supported until Oct 2026. |
| TanStack Query | SWR | SWR is lighter but lacks query invalidation, mutations API, and devtools. TanStack Query is the PRD-specified choice. |
| Tailwind v4 | Tailwind v3 | v3 still works but v4 is faster, simpler config, and is the current stable. New project should use v4. |
| date-fns | Intl.RelativeTimeFormat | Native API works for "X minutes ago" but requires manual unit calculation. date-fns `formatDistanceToNow` is a single tree-shakeable import (~2KB). Either works; native API avoids a dependency. |
| Vitest | Jest | Jest is heavier, slower, doesn't natively support ESM. Vitest is the Next.js docs recommendation. |

**Installation:**
```bash
# Scaffold (run from repo root, into web/ directory)
npx create-next-app@15 web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Additional dependencies
cd web
npm install @tanstack/react-query
npm install -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom vite-tsconfig-paths
```

Note: `create-next-app@15` pins to Next.js 15 LTS. Using `@latest` would install Next.js 16.

## Architecture Patterns

### Recommended Project Structure
```
web/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout (wraps Providers)
│   │   ├── page.tsx            # Home page (hall feed)
│   │   └── globals.css         # Tailwind @import + @theme customization
│   ├── components/
│   │   ├── ui/                 # Generic reusable (Badge, Skeleton, etc.)
│   │   ├── hall-card.tsx       # Single dining hall card
│   │   ├── meal-tabs.tsx       # Breakfast/Lunch/Dinner tab switcher
│   │   ├── station-list.tsx    # Station groupings with menu items
│   │   ├── menu-item.tsx       # Single item with dietary icons
│   │   ├── date-bar.tsx        # 7-day date navigation
│   │   ├── open-now-toggle.tsx # "What's Open Now" filter
│   │   └── stale-banner.tsx    # "Last updated X ago" indicator
│   ├── lib/
│   │   ├── api.ts              # API client (fetch wrappers for each endpoint)
│   │   ├── query-provider.tsx  # 'use client' QueryClientProvider wrapper
│   │   ├── hooks.ts            # useHalls(), useMenu(), useOpenNow() query hooks
│   │   ├── types.ts            # TypeScript types matching API response shapes
│   │   └── constants.ts        # Hall colors, dietary tag icon map, meal periods
│   └── __tests__/              # Component tests (Vitest)
├── public/                     # Static assets (dietary icons if SVG)
├── vitest.config.mts           # Vitest configuration
├── postcss.config.mjs          # PostCSS with @tailwindcss/postcss
├── next.config.ts              # Next.js config (minimal)
├── tsconfig.json               # TypeScript config
└── package.json
```

### Pattern 1: TanStack Query Provider for App Router
**What:** Wrap the app in a client-side QueryClientProvider via a dedicated `'use client'` component.
**When to use:** Always -- required for TanStack Query hooks to work.
**Example:**
```typescript
// src/lib/query-provider.tsx
// Source: https://tanstack.com/query/v5/docs/framework/react/guides/advanced-ssr
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 min before refetch
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

```typescript
// src/app/layout.tsx
import { QueryProvider } from '@/lib/query-provider'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
```

### Pattern 2: Custom Query Hooks for Each Endpoint
**What:** Wrap `useQuery` calls in domain-specific hooks that encapsulate query keys, fetch functions, and types.
**When to use:** Every API call should go through a custom hook.
**Example:**
```typescript
// src/lib/hooks.ts
'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchHalls, fetchMenu, fetchOpenNow } from './api'
import type { HallResponse, MenuResponse, OpenHallResponse } from './types'

export function useHalls() {
  return useQuery<HallResponse[]>({
    queryKey: ['halls'],
    queryFn: fetchHalls,
    staleTime: 5 * 60 * 1000, // halls change rarely
  })
}

export function useMenu(hallId: string, date: string, meal: string) {
  return useQuery<MenuResponse>({
    queryKey: ['menu', hallId, date, meal],
    queryFn: () => fetchMenu(hallId, date, meal),
    enabled: !!hallId && !!date && !!meal,
  })
}

export function useOpenNow() {
  return useQuery<OpenHallResponse[]>({
    queryKey: ['open-now'],
    queryFn: fetchOpenNow,
    refetchInterval: 60 * 1000, // poll every 60s
  })
}
```

### Pattern 3: API Client with Base URL from Environment
**What:** Centralize all API calls in one module that reads `NEXT_PUBLIC_API_URL`.
**When to use:** Every external API call.
**Example:**
```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const fetchHalls = () => apiFetch<HallResponse[]>('/api/v2/halls/')
export const fetchMenu = (hallId: string, date: string, meal: string) =>
  apiFetch<MenuResponse>(`/api/v2/menus/?hall_id=${hallId}&date=${date}&meal=${meal}`)
export const fetchOpenNow = () => apiFetch<OpenHallResponse[]>('/api/v2/open-now/')
```

### Pattern 4: Tailwind v4 Custom Theme for School Colors
**What:** Define school colors as CSS custom properties via `@theme` directive.
**When to use:** Defining the per-hall color palette.
**Example:**
```css
/* src/app/globals.css */
@import "tailwindcss";

@theme {
  --color-hmc: #F5C518;
  --color-cmc: #800000;
  --color-scripps: #2E4057;
  --color-pitzer: #FF6600;
  --color-pomona: #003B5C;
}
```
Usage: `bg-hmc`, `bg-cmc`, `text-pomona`, etc.

### Pattern 5: Dark Mode via System Preference
**What:** Tailwind v4 applies `dark:` variants based on `prefers-color-scheme` by default. No configuration needed.
**When to use:** FE-10 requirement.
**Example:**
```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <!-- content -->
</div>
```
No `tailwind.config.js` dark mode setting required -- v4 defaults to `prefers-color-scheme`.

### Anti-Patterns to Avoid
- **Server Components for dynamic data:** All menu data is user-specific (date, meal selection). Use `'use client'` components with TanStack Query, not server components or `fetch()` in server components. The PROJECT.md explicitly states "Client-side rendering" as a locked decision.
- **Prop drilling API data:** Use TanStack Query hooks directly in each component, not prop chains from a parent fetch.
- **Inline fetch calls:** Always go through `api.ts` -> custom hooks. Never call `fetch()` directly in components.
- **Hardcoded API URL:** Use `NEXT_PUBLIC_API_URL` environment variable, not a literal URL.
- **Dynamic school colors via `bg-[${color}]`:** Tailwind cannot generate classes for dynamic values at build time. Use the `@theme` CSS variables approach or a `style` prop for the hex value.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data fetching + caching | Custom fetch + useState + useEffect | TanStack Query `useQuery` | Handles loading, error, stale, refetch, dedup, garbage collection |
| "Last updated X ago" | Manual date math | `Intl.RelativeTimeFormat` or `date-fns/formatDistanceToNow` | Localization, edge cases (future dates, just now) |
| Dark mode system | Custom JS media query listener | Tailwind `dark:` variant (prefers-color-scheme default) | Zero-config, SSR-safe, no FOUC |
| Loading skeletons | Custom shimmer CSS | Tailwind `animate-pulse` on placeholder divs | Built-in, consistent |
| Date navigation logic | Manual date arithmetic | `Date` API or date-fns `addDays` | Timezone edge cases, month boundaries |
| Responsive breakpoints | Custom media queries | Tailwind responsive prefixes (`sm:`, `md:`, `lg:`) | Consistent, maintainable |

**Key insight:** This is a read-only data display app. TanStack Query + Tailwind handle 90% of the complexity. The custom code is mostly composition (arranging components, mapping data to UI).

## Common Pitfalls

### Pitfall 1: Dynamic Tailwind Class Names
**What goes wrong:** Using template literals like `` `bg-${hall.color}` `` produces classes Tailwind never sees at build time, so they are not generated.
**Why it happens:** Tailwind scans source files for complete class strings. Dynamic concatenation breaks this.
**How to avoid:** Two options: (a) Define all school colors in `@theme` and use a lookup map `{ hmc: 'bg-hmc', cmc: 'bg-cmc', ... }`, or (b) use inline `style={{ backgroundColor: hall.color }}` for the hex value from the API.
**Warning signs:** Cards render without background color; classes appear in source but not in generated CSS.

### Pitfall 2: QueryClient Created on Every Render
**What goes wrong:** Creating `new QueryClient()` at module level or in render body causes cache to reset on navigation.
**Why it happens:** In App Router, module-level code can re-execute. React strict mode double-renders.
**How to avoid:** Use `useState(() => new QueryClient(...))` inside the provider component (see Pattern 1).
**Warning signs:** Data flashes on every navigation; loading spinners appear for already-fetched data.

### Pitfall 3: Missing 'use client' Directive
**What goes wrong:** Components using `useQuery`, `useState`, or `useEffect` fail with "hooks can only be used in client components" error.
**Why it happens:** App Router defaults all components to server components. Hooks require client components.
**How to avoid:** Add `'use client'` to every file that uses React hooks or browser APIs.
**Warning signs:** Build error or runtime error about hooks in server components.

### Pitfall 4: CORS Blocking API Calls
**What goes wrong:** Browser blocks requests to `localhost:8000` from `localhost:3000`.
**Why it happens:** Different ports = different origins. CORS policy blocks cross-origin requests.
**How to avoid:** Backend already has `allowed_origins: ["http://localhost:3000"]` in `app/config.py`. Ensure the env var is set correctly in production (`FIVEC_ALLOWED_ORIGINS`).
**Warning signs:** Network tab shows "CORS error"; API calls fail silently in the browser.

### Pitfall 5: Tailwind v4 PostCSS Plugin Name
**What goes wrong:** Using `tailwindcss` as the PostCSS plugin name (v3 style) instead of `@tailwindcss/postcss`.
**Why it happens:** Old tutorials and muscle memory from v3.
**How to avoid:** PostCSS config must use `"@tailwindcss/postcss": {}`, and CSS must use `@import "tailwindcss"` not `@tailwind base/components/utilities`.
**Warning signs:** Build error: "It looks like you're trying to use tailwindcss directly as a PostCSS plugin."

### Pitfall 6: Stale Date in Client-Side App
**What goes wrong:** User opens the app before midnight, crosses midnight, and the "today" date is now yesterday.
**Why it happens:** Date is computed once on page load and never updated.
**How to avoid:** Compute "today" in the date bar component or in the query key so it updates. Use the API's `America/Los_Angeles` timezone assumption (menus are Pacific time).
**Warning signs:** After midnight, app shows yesterday's menu as "today".

### Pitfall 7: Vitest Cannot Test Async Server Components
**What goes wrong:** Attempting to test async server components fails.
**Why it happens:** React Testing Library does not yet support async server components.
**How to avoid:** Only test client components with Vitest. This app is mostly client components anyway. Use E2E tests (Playwright) for full page verification if needed later.
**Warning signs:** Test errors about unsupported async components.

## Code Examples

Verified patterns from official sources:

### API Type Definitions (Matching Backend Schemas)
```typescript
// src/lib/types.ts
// Mirrors backend app/schemas/*.py exactly

export interface HallResponse {
  id: string
  name: string
  college: string
  vendor_type: string
  color: string | null
}

export interface MenuItemResponse {
  name: string
  tags: string[]
}

export interface StationResponse {
  name: string
  items: MenuItemResponse[]
}

export interface MenuResponse {
  hall_id: string
  date: string
  meal: string
  stations: StationResponse[]
  is_stale: boolean
  fetched_at: string | null
}

export interface OpenHallResponse {
  id: string
  name: string
  college: string
  color: string | null
  current_meal: string
}
```

### Hall Card Component (FE-01, FE-09, FE-06)
```typescript
// src/components/hall-card.tsx
'use client'

import type { HallResponse } from '@/lib/types'
import { MealTabs } from './meal-tabs'

// Map college to Tailwind @theme color class
const COLLEGE_BG: Record<string, string> = {
  hmc: 'bg-hmc',
  cmc: 'bg-cmc',
  scripps: 'bg-scripps',
  pitzer: 'bg-pitzer',
  pomona: 'bg-pomona',
}

interface HallCardProps {
  hall: HallResponse
  date: string
  isOpen: boolean
  currentMeal?: string
}

export function HallCard({ hall, date, isOpen, currentMeal }: HallCardProps) {
  const bgClass = COLLEGE_BG[hall.college] ?? 'bg-gray-500'

  return (
    <div className={`${bgClass} rounded-2xl p-4 text-white`}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-bold">{hall.name}</h2>
        {isOpen ? (
          <span className="bg-green-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
            Open
          </span>
        ) : (
          <span className="bg-gray-600 text-gray-300 text-xs font-semibold px-2 py-1 rounded-full">
            Closed
          </span>
        )}
      </div>
      <MealTabs hallId={hall.id} date={date} defaultMeal={currentMeal} />
    </div>
  )
}
```

### Date Bar Component (FE-08)
```typescript
// src/components/date-bar.tsx
'use client'

import { useState } from 'react'

function formatDateLabel(date: Date): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(date)
  target.setHours(0, 0, 0, 0)
  const diff = Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  return target.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function getDateRange(): Date[] {
  const dates: Date[] = []
  const today = new Date()
  for (let i = 0; i < 7; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    dates.push(d)
  }
  return dates
}

interface DateBarProps {
  selectedDate: string // YYYY-MM-DD
  onDateChange: (date: string) => void
}

export function DateBar({ selectedDate, onDateChange }: DateBarProps) {
  const dates = getDateRange()

  return (
    <div className="flex gap-2 overflow-x-auto py-2 px-1 no-scrollbar">
      {dates.map((d) => {
        const iso = d.toISOString().slice(0, 10)
        const isSelected = iso === selectedDate
        return (
          <button
            key={iso}
            onClick={() => onDateChange(iso)}
            className={`shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors
              ${isSelected
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
              }`}
          >
            {formatDateLabel(d)}
          </button>
        )
      })}
    </div>
  )
}
```

### Stale Data Banner (FE-12)
```typescript
// src/components/stale-banner.tsx
'use client'

function timeAgo(isoString: string): string {
  const seconds = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

  if (seconds < 60) return rtf.format(-seconds, 'second')
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return rtf.format(-minutes, 'minute')
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return rtf.format(-hours, 'hour')
  const days = Math.floor(hours / 24)
  return rtf.format(-days, 'day')
}

interface StaleBannerProps {
  fetchedAt: string | null
  isStale: boolean
}

export function StaleBanner({ fetchedAt, isStale }: StaleBannerProps) {
  if (!isStale || !fetchedAt) return null

  return (
    <div className="bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-xs px-3 py-1.5 rounded-lg">
      Last updated {timeAgo(fetchedAt)}
    </div>
  )
}
```

### Vitest Config
```typescript
// vitest.config.mts
// Source: https://nextjs.org/docs/app/guides/testing/vitest
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test-setup.ts',
  },
})
```

```typescript
// src/test-setup.ts
import '@testing-library/jest-dom/vitest'
```

### Component Test Example (TEST-03)
```typescript
// src/__tests__/stale-banner.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StaleBanner } from '@/components/stale-banner'

describe('StaleBanner', () => {
  it('renders nothing when not stale', () => {
    const { container } = render(
      <StaleBanner isStale={false} fetchedAt="2026-02-09T12:00:00Z" />
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('shows time ago when stale', () => {
    const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString()
    render(<StaleBanner isStale={true} fetchedAt={oneHourAgo} />)
    expect(screen.getByText(/last updated/i)).toBeInTheDocument()
  })
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind v3 `tailwind.config.js` | Tailwind v4 CSS-first `@theme` + `@import "tailwindcss"` | Jan 2025 | No JS config file; faster builds; simpler setup |
| Tailwind v3 `@tailwind base/components/utilities` | Tailwind v4 `@import "tailwindcss"` | Jan 2025 | Single import replaces three directives |
| Next.js Pages Router | Next.js App Router | Next.js 13+ (2023) | File-based routing with layouts, server components default |
| React Query v4 `cacheTime` | TanStack Query v5 `gcTime` | Oct 2023 | Renamed for clarity; v4 API deprecated |
| React Query v4 overloads | TanStack Query v5 single-object API | Oct 2023 | `useQuery({ queryKey, queryFn })` always, no positional args |
| Next.js 14 (PRD-specified) | Next.js 15 LTS | Oct 2024 | 14 is EOL as of Oct 2025; 15 is current LTS |
| `tailwindcss` PostCSS plugin | `@tailwindcss/postcss` | Tailwind v4 (Jan 2025) | Different package name; old name errors out |

**Deprecated/outdated:**
- Next.js 14: End of life since Oct 2025. Must use 15 or 16.
- `tailwind.config.js`: Still works in v4 via legacy compat, but `@theme` in CSS is the standard path.
- TanStack Query v4: Still installable but v5 is the current stable.

## Open Questions

1. **Dining hall hours endpoint (FE-07)**
   - What we know: The current API has no endpoint that returns dining hall hours (schedule by day-of-week). `HallResponse` returns `{id, name, college, vendor_type, color}`. The `open-now` endpoint only returns currently-open halls.
   - What's unclear: Whether to add hours to `HallResponse`, create a new `/api/v2/halls/{id}/hours` endpoint, or defer FE-07 to a later plan.
   - Recommendation: Add a `hours` field to the `/api/v2/halls` response or create a new endpoint. This requires a small backend change in Phase 3 scope. Could be as simple as a new query in `halls.py` router that joins `DiningHours` to the response.

2. **School color contrast in dark mode**
   - What we know: School colors (gold, maroon, dark navy, orange, dark blue) are used as card backgrounds. Some (HMC gold, Pitzer orange) are very bright; others (Pomona navy, Scripps teal) are very dark.
   - What's unclear: Whether the same hex colors work well in both light and dark mode for readability.
   - Recommendation: Test the exact colors at implementation time. May need slight opacity/shade adjustments via Tailwind's opacity modifier (`bg-hmc/90`) for dark mode.

3. **Meal period list per hall**
   - What we know: Different halls support different meals (Oldenborg is lunch-only; Collins has late night). The API `menus` endpoint returns 404 for invalid hall+meal combos.
   - What's unclear: How the frontend knows which meal tabs to show per hall without a dedicated endpoint.
   - Recommendation: Hardcode the known meal periods per hall in a frontend constant (matching the backend's `HALL_CONFIG` pattern), or derive from a new API response. Since this data rarely changes, a frontend constant is acceptable for v1.

4. **Date timezone handling**
   - What we know: The backend uses `America/Los_Angeles` timezone for all date/time logic. The frontend sends `date` as `YYYY-MM-DD` string.
   - What's unclear: If a user in a different timezone opens the app after midnight Pacific, should "today" be their local date or Pacific date?
   - Recommendation: Use Pacific time for "today" to match the backend's assumption. The API date parameter is a date string, and the backend parses it relative to Pacific. Use `toLocaleDateString` with `timeZone: 'America/Los_Angeles'` to derive "today".

## Sources

### Primary (HIGH confidence)
- Next.js official docs (https://nextjs.org/docs/app/guides/testing/vitest) -- Vitest setup guide
- Next.js EOL (https://endoflife.date/nextjs) -- Version 15 LTS until Oct 2026, version 14 EOL
- Tailwind CSS v4 official docs (https://tailwindcss.com/docs/dark-mode) -- Dark mode via `prefers-color-scheme`
- Tailwind CSS v4 official docs (https://tailwindcss.com/docs/customizing-colors) -- `@theme` directive for custom colors
- Tailwind CSS v4 install guide (https://tailwindcss.com/docs/guides/nextjs) -- PostCSS setup with `@tailwindcss/postcss`
- TanStack Query v5 docs (https://tanstack.com/query/v5/docs/framework/react/overview) -- QueryClientProvider, useQuery API
- TanStack Query Next.js guide (https://tanstack.com/query/latest/docs/framework/react/guides/advanced-ssr) -- App Router provider pattern
- MDN Intl.RelativeTimeFormat (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/RelativeTimeFormat) -- Native relative time API

### Secondary (MEDIUM confidence)
- Next.js 15 vs 16 migration (https://nextjs.org/docs/app/guides/upgrading/version-16) -- Breaking changes in 16 (middleware->proxy, Turbopack default)
- npm create-next-app (https://www.npmjs.com/package/create-next-app) -- Latest version is 16.1.6
- npm @tanstack/react-query (https://www.npmjs.com/package/@tanstack/react-query) -- Latest version 5.90.x
- Vitest npm (https://www.npmjs.com/package/vitest) -- Latest version 4.x

### Tertiary (LOW confidence)
- None -- all findings verified with official sources.

## Existing Backend API Contract (Reference)

Endpoints the frontend will consume:

| Endpoint | Method | Params | Response |
|----------|--------|--------|----------|
| `/api/v2/halls/` | GET | none | `HallResponse[]` -- `{id, name, college, vendor_type, color}` |
| `/api/v2/menus/` | GET | `hall_id`, `date` (YYYY-MM-DD), `meal` | `MenuResponse` -- `{hall_id, date, meal, stations[], is_stale, fetched_at}` |
| `/api/v2/open-now/` | GET | none | `OpenHallResponse[]` -- `{id, name, college, color, current_meal}` |

CORS: Backend allows `http://localhost:3000` by default (configurable via `FIVEC_ALLOWED_ORIGINS`).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries are mature, well-documented, and verified with official sources. Version compatibility confirmed.
- Architecture: HIGH -- Patterns follow official TanStack Query + Next.js App Router documentation. Client-side rendering approach is explicitly supported.
- Pitfalls: HIGH -- All pitfalls verified against known issues in official docs and community discussions.

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days -- stable ecosystem, no major releases expected)
