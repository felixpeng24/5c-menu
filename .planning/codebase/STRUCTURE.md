# Codebase Structure

**Analysis Date:** 2026-02-07

## Directory Layout

```
5c-menu/
├── backend/                # FastAPI backend (Python)
│   ├── main.py            # FastAPI app entry point
│   ├── models/            # SQLAlchemy ORM models
│   │   ├── dining_hall.py
│   │   ├── menu.py
│   │   └── hours.py
│   ├── parsers/           # Menu scraper implementations
│   │   ├── base.py        # Abstract MenuParser base class
│   │   ├── sodexo.py      # Hoch-Shanahan parser
│   │   ├── bonappetit.py  # Collins, Malott, McConnell parser
│   │   └── pomona.py      # Frank, Frary, Oldenborg parser
│   ├── routes/            # API endpoints organized by resource
│   │   ├── halls.py       # GET /api/v2/halls, /api/v2/open-now
│   │   ├── menus.py       # GET /api/v2/menus
│   │   ├── crowding.py    # GET /api/v2/crowding, POST /api/v2/location
│   │   └── admin.py       # POST /api/v2/admin/* (password-protected)
│   ├── services/          # Business logic layer
│   │   ├── menu_service.py
│   │   ├── crowding_service.py
│   │   ├── hours_service.py
│   │   └── auth_service.py
│   ├── jobs/              # Background tasks
│   │   └── aggregation.py # Crowding aggregation job (runs every 30s)
│   ├── config.py          # Environment config, database URL, Redis URL
│   ├── database.py        # SQLAlchemy session factory, DB init
│   ├── cache.py           # Redis client wrapper
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Container image (for Railway deployment)
│
├── web/                    # Next.js frontend (React/TypeScript)
│   ├── app/               # Next.js App Router
│   │   ├── layout.tsx     # Root layout with providers
│   │   ├── page.tsx       # Home (hall list + "What's Open Now")
│   │   ├── hall/
│   │   │   └── [id]/
│   │   │       └── page.tsx  # Hall detail (menus, hours, crowding)
│   │   ├── settings/
│   │   │   └── page.tsx   # Settings (college preference, dark mode)
│   │   └── admin/         # Admin panel (password-protected layout)
│   │       ├── layout.tsx
│   │       ├── page.tsx   # Admin dashboard
│   │       ├── hours/
│   │       │   └── page.tsx
│   │       └── overrides/
│   │           └── page.tsx
│   ├── components/        # Reusable React components
│   │   ├── HallCard.tsx   # Hall list item with crowding badge
│   │   ├── MenuDisplay.tsx
│   │   ├── CrowdingBadge.tsx
│   │   ├── DateNavigation.tsx
│   │   └── Navigation.tsx  # Header/footer navigation
│   ├── hooks/             # Custom React hooks
│   │   ├── useMenus.ts    # React Query hook for menu fetching
│   │   ├── useCrowding.ts
│   │   ├── useHalls.ts
│   │   └── useDarkMode.ts
│   ├── lib/               # Utilities and helpers
│   │   ├── api.ts         # Fetch wrapper with error handling
│   │   ├── queryClient.ts # React Query client config
│   │   └── time.ts        # Date/time utilities
│   ├── styles/            # Tailwind + global CSS
│   │   └── globals.css
│   ├── public/            # Static assets
│   │   └── favicon.ico
│   ├── package.json       # Dependencies: next, react, tailwind, react-query
│   ├── tsconfig.json      # TypeScript config
│   ├── tailwind.config.ts # Tailwind CSS config
│   ├── next.config.ts     # Next.js config (API routes, redirects)
│   └── .env.example       # Example env vars (NEXT_PUBLIC_API_URL)
│
├── mobile/                 # Expo React Native app (TypeScript)
│   ├── app/               # Expo Router navigation
│   │   ├── _layout.tsx    # Root layout with navigation stack
│   │   ├── index.tsx      # Home (hall list)
│   │   ├── hall/
│   │   │   └── [id].tsx   # Hall detail screen
│   │   ├── settings/
│   │   │   └── index.tsx  # Settings screen (location toggle, college preference)
│   │   └── admin/         # Admin screens (if needed for mobile)
│   ├── components/        # React Native components
│   │   ├── HallListItem.tsx
│   │   ├── MenuDisplay.tsx
│   │   ├── CrowdingBadge.tsx
│   │   └── DateNavigation.tsx
│   ├── hooks/             # Custom hooks
│   │   ├── useMenus.ts    # React Query hook
│   │   ├── useCrowding.ts
│   │   ├── useLocation.ts # expo-location integration
│   │   └── useStorage.ts  # AsyncStorage integration
│   ├── lib/               # Utilities
│   │   ├── api.ts         # API client (shared with web where possible)
│   │   ├── queryClient.ts # React Query config
│   │   ├── geofence.ts    # Geofence distance calculation
│   │   └── storage.ts     # AsyncStorage wrapper
│   ├── constants/         # App constants
│   │   ├── halls.ts       # Hall definitions (geofences, colors)
│   │   └── config.ts      # API endpoint, ping interval, etc.
│   ├── app.json           # Expo config (app name, version, permissions)
│   ├── package.json       # Dependencies: expo, react-native, react-query
│   ├── tsconfig.json      # TypeScript config
│   └── .env.example       # Example env vars (API_URL)
│
├── .planning/             # GSD planning documents
│   └── codebase/          # Architecture + conventions docs
│       ├── ARCHITECTURE.md
│       ├── STRUCTURE.md
│       ├── CONVENTIONS.md
│       ├── TESTING.md
│       ├── STACK.md
│       ├── INTEGRATIONS.md
│       └── CONCERNS.md
│
├── PRD.md                 # Product Requirements Document
├── .gitignore             # Ignore node_modules, .env, .next, etc.
└── README.md              # Project overview (to be created)
```

## Directory Purposes

**backend/**
- Purpose: Python FastAPI application serving API endpoints
- Contains: Route handlers, database models, parsers, business logic, background jobs
- Key files: `backend/main.py` (app entry), `backend/routes/*.py` (endpoints), `backend/parsers/*.py` (menu scrapers)

**backend/models/**
- Purpose: SQLAlchemy ORM models mapping to PostgreSQL tables
- Contains: DiningHall, Menu, DiningHours, DiningHoursOverride models
- Key files: `backend/models/dining_hall.py`, `backend/models/menu.py`, `backend/models/hours.py`

**backend/parsers/**
- Purpose: Pluggable menu parser implementations for each dining vendor
- Contains: Abstract base class and concrete parsers (Sodexo, BonAppetit, Pomona)
- Key files: `backend/parsers/base.py`, `backend/parsers/sodexo.py`, `backend/parsers/bonappetit.py`, `backend/parsers/pomona.py`

**backend/routes/**
- Purpose: API endpoint handlers organized by resource type
- Contains: Request handlers, input validation, response formatting
- Key files: `backend/routes/halls.py`, `backend/routes/menus.py`, `backend/routes/crowding.py`, `backend/routes/admin.py`

**backend/services/**
- Purpose: Business logic layer between routes and data access
- Contains: Menu fetching logic, crowding calculations, authentication
- Key files: `backend/services/menu_service.py`, `backend/services/crowding_service.py`

**backend/jobs/**
- Purpose: Background tasks and scheduled jobs
- Contains: Crowding aggregation job (runs every 30 seconds)
- Key files: `backend/jobs/aggregation.py`

**web/**
- Purpose: Next.js 14 frontend with App Router
- Contains: Pages, components, hooks, styling, API client logic
- Key files: `web/app/page.tsx` (home), `web/app/hall/[id]/page.tsx` (detail), `web/app/admin/` (admin panel)

**web/app/**
- Purpose: Next.js App Router directory defining routes and layouts
- Contains: Page components, nested routes, layouts
- Key files: `web/app/layout.tsx` (root), `web/app/page.tsx` (home), `web/app/hall/[id]/page.tsx` (detail)

**web/components/**
- Purpose: Reusable React components shared across pages
- Contains: UI components like HallCard, MenuDisplay, CrowdingBadge, DateNavigation
- Key files: `web/components/HallCard.tsx`, `web/components/MenuDisplay.tsx`, `web/components/CrowdingBadge.tsx`

**web/hooks/**
- Purpose: Custom React hooks encapsulating data fetching and state management
- Contains: React Query hooks for menus, crowding, halls; theme hook
- Key files: `web/hooks/useMenus.ts`, `web/hooks/useCrowding.ts`, `web/hooks/useHalls.ts`

**web/lib/**
- Purpose: Utility functions and configuration
- Contains: API client, React Query config, date/time utilities
- Key files: `web/lib/api.ts` (fetch wrapper), `web/lib/queryClient.ts` (React Query setup)

**mobile/**
- Purpose: Expo React Native app for iOS and Android
- Contains: Screens, components, hooks, native integrations
- Key files: `mobile/app/_layout.tsx` (root navigation), `mobile/app/index.tsx` (home), `mobile/app/hall/[id].tsx` (detail)

**mobile/app/**
- Purpose: Expo Router navigation definition
- Contains: Screen files, nested routes, layout files
- Key files: `mobile/app/_layout.tsx` (root), `mobile/app/index.tsx` (home screen)

**mobile/components/**
- Purpose: React Native components specific to mobile UI
- Contains: Native versions of shared components (HallListItem, MenuDisplay, etc.)
- Key files: `mobile/components/HallListItem.tsx`, `mobile/components/CrowdingBadge.tsx`

**mobile/hooks/**
- Purpose: Custom hooks including location and storage integration
- Contains: React Query hooks + native-specific hooks (useLocation, useStorage)
- Key files: `mobile/hooks/useLocation.ts` (expo-location), `mobile/hooks/useStorage.ts` (AsyncStorage)

**mobile/constants/**
- Purpose: App-wide constants and configuration
- Contains: Hall definitions (coordinates, geofences), API endpoint, ping interval
- Key files: `mobile/constants/halls.ts`, `mobile/constants/config.ts`

**.planning/codebase/**
- Purpose: GSD planning documents for architecture, conventions, testing, concerns
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, STACK.md, INTEGRATIONS.md, CONCERNS.md
- Key files: All .md files consumed by GSD orchestrator

## Key File Locations

**Entry Points:**
- Backend: `backend/main.py` - FastAPI application root
- Web: `web/app/page.tsx` - Home page (hall list)
- Mobile: `mobile/app/index.tsx` - Home screen

**Configuration:**
- Backend: `backend/config.py` - Environment variables, database URL, Redis URL
- Backend: `backend/database.py` - SQLAlchemy session factory
- Web: `web/next.config.ts` - Next.js configuration
- Web: `web/tailwind.config.ts` - Tailwind CSS theme
- Mobile: `mobile/app.json` - Expo configuration
- Mobile: `mobile/constants/config.ts` - API endpoint, intervals

**Core Logic:**
- Menu fetching: `backend/services/menu_service.py`, `backend/routes/menus.py`
- Menu parsing: `backend/parsers/sodexo.py`, `backend/parsers/bonappetit.py`, `backend/parsers/pomona.py`
- Crowding: `backend/services/crowding_service.py`, `backend/routes/crowding.py`, `backend/jobs/aggregation.py`
- API client: `web/lib/api.ts`, `mobile/lib/api.ts`
- React Query setup: `web/lib/queryClient.ts`, `mobile/lib/queryClient.ts`

**Testing:**
- Backend: `backend/tests/` (pytest) - Unit tests for parsers, services, routes
- Web: `web/__tests__/` or `web/app/**/*.test.tsx` (Jest/Vitest) - Component and hook tests
- Mobile: `mobile/__tests__/` (Jest/Detox) - Component tests and E2E tests

**Styling:**
- Global CSS: `web/styles/globals.css`
- Tailwind config: `web/tailwind.config.ts`
- Component styles: Co-located with components (Tailwind classes inline)
- Mobile styling: React Native StyleSheet or NativeWind (Tailwind for React Native)

## Naming Conventions

**Files:**

- **Components** (React/React Native): PascalCase, `.tsx` extension
  - Example: `HallCard.tsx`, `MenuDisplay.tsx`, `CrowdingBadge.tsx`

- **Hooks**: camelCase with `use` prefix, `.ts` or `.tsx` extension
  - Example: `useMenus.ts`, `useCrowding.ts`, `useLocation.ts`

- **API routes** (backend): lowercase with underscores, `.py` extension
  - Example: `menu_service.py`, `crowding_service.py`, `aggregation.py`

- **Route files** (backend): lowercase with underscores, organized in `routes/` directory
  - Example: `routes/halls.py`, `routes/menus.py`, `routes/crowding.py`

- **Utilities**: camelCase, `.ts` extension
  - Example: `api.ts`, `queryClient.ts`, `geofence.ts`

- **Configuration**: lowercase with underscores (Python) or camelCase (TypeScript)
  - Example: `config.py`, `tailwind.config.ts`, `next.config.ts`

**Directories:**

- **Feature directories** (plural): lowercase
  - Example: `components/`, `hooks/`, `services/`, `routes/`, `parsers/`

- **Feature-specific nested routes** (Next.js/Expo Router): lowercase with brackets for dynamic segments
  - Example: `hall/[id]/`, `admin/`, `settings/`

- **Models directory**: `models/` (Python)

- **Constants directory**: `constants/` (JavaScript/TypeScript)

## Where to Add New Code

**New Feature (Menu-related):**
- Backend logic: `backend/services/menu_service.py`
- API route: `backend/routes/menus.py`
- Web component: `web/components/Menu*.tsx`
- Web hook: `web/hooks/useMenus.ts`
- Mobile component: `mobile/components/Menu*.tsx`
- Tests: `backend/tests/test_menu_service.py`, `web/__tests__/useMenus.test.ts`

**New Menu Parser (for new dining vendor):**
- Parser implementation: `backend/parsers/{vendor}.py` (inherit from `parsers/base.py`)
- Add to hall configuration: `backend/models/dining_hall.py` (assign parser_type)
- Tests: `backend/tests/parsers/test_{vendor}.py`

**New API Endpoint:**
- Route handler: `backend/routes/{resource}.py`
- Service logic: `backend/services/{resource}_service.py`
- Tests: `backend/tests/test_{resource}.py`

**New Frontend Page (Web):**
- Page file: `web/app/{path}/page.tsx`
- Components: `web/components/{FeatureName}*.tsx`
- Hooks: `web/hooks/use{FeatureName}.ts`
- Tests: `web/__tests__/{path}.test.tsx`

**New Mobile Screen:**
- Screen file: `mobile/app/{path}.tsx`
- Components: `mobile/components/{FeatureName}*.tsx`
- Hooks: `mobile/hooks/use{FeatureName}.ts`
- Tests: `mobile/__tests__/{path}.test.tsx`

**New Utility:**
- Shared utilities: `web/lib/` or `mobile/lib/` (or both if identical)
- Backend utilities: `backend/` (new file or existing service)

**Constants:**
- Hall definitions, geofences: `mobile/constants/halls.ts`
- Config values: `backend/config.py`, `mobile/constants/config.ts`

## Special Directories

**.planning/codebase/**
- Purpose: GSD architecture and convention documents
- Generated: No (manually maintained)
- Committed: Yes (part of repo for future phases)
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, STACK.md, INTEGRATIONS.md, CONCERNS.md

**backend/tests/**
- Purpose: pytest test suite for backend logic
- Generated: No (developer-created)
- Committed: Yes (part of repo)
- Structure: Mirror `backend/` structure (e.g., `tests/parsers/test_sodexo.py` mirrors `parsers/sodexo.py`)

**web/public/**
- Purpose: Static assets served by Next.js
- Generated: No (developer-created or third-party)
- Committed: Yes
- Contents: favicon.ico, images, fonts

**mobile/.expo/ and mobile/android/ and mobile/ios/**
- Purpose: Expo build artifacts and native code
- Generated: Yes (Expo CLI generates during `expo prebuild`)
- Committed: No (in .gitignore)

**backend/__pycache__/ and backend/*.egg-info/**
- Purpose: Python build and cache artifacts
- Generated: Yes (Python during import and install)
- Committed: No (in .gitignore)

**web/.next/ and web/out/**
- Purpose: Next.js build output and static export
- Generated: Yes (Next.js build process)
- Committed: No (in .gitignore)

---

*Structure analysis: 2026-02-07*
