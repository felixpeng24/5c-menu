# Architecture

**Analysis Date:** 2026-02-07

## Pattern Overview

**Overall:** Distributed multi-platform architecture with decoupled backend API and frontend clients.

**Key Characteristics:**
- Backend API-first design (FastAPI) serving web and mobile clients
- Cross-platform UI implementation (React/Next.js for web, React Native/Expo for mobile)
- Real-time crowding aggregation using Redis session store
- Pluggable menu parser system for multiple dining vendor APIs
- Client-side caching for offline menu browsing

## Layers

**API Layer:**
- Purpose: Expose RESTful endpoints for menu data, crowding levels, and admin operations
- Location: `backend/` (to be implemented)
- Contains: FastAPI route handlers, request validation, response serialization
- Depends on: Database layer, cache layer, parser layer
- Used by: Web frontend, mobile app

**Database Layer:**
- Purpose: Persistent storage of dining halls, hours, menus, and overrides
- Location: PostgreSQL (external service)
- Contains: Dining halls table, dining hours table, menu cache table, overrides table
- Depends on: None (authority of record)
- Used by: API layer, parsers

**Cache Layer:**
- Purpose: High-speed storage for menu data, crowding snapshots, and ephemeral location pings
- Location: Redis (external service)
- Contains: Menu cache (30-minute TTL), crowding snapshots (60-second TTL), location pings (120-second TTL)
- Depends on: None
- Used by: API layer, aggregation job

**Parser Layer:**
- Purpose: Extract menu data from external dining vendor websites
- Location: `backend/parsers/` (to be implemented)
- Contains: `SodexoParser`, `BonAppetitParser`, `PomonaParser` classes
- Depends on: HTTP client for scraping, data transformation utilities
- Used by: API layer (on cache miss)

**Frontend Web Layer:**
- Purpose: Responsive web interface for menu browsing and crowding display
- Location: `web/` (to be implemented)
- Contains: Next.js pages, React components, Tailwind styling, React Query client
- Depends on: API layer, AsyncStorage (browser localStorage)
- Used by: Web browsers (desktop and mobile browsers)

**Frontend Mobile Layer:**
- Purpose: Native-like mobile interface for iOS and Android
- Location: `mobile/` (to be implemented)
- Contains: Expo screens, React Native components, navigation stack, AsyncStorage
- Depends on: API layer, location services, native device APIs
- Used by: iOS/Android apps

**Admin Panel:**
- Purpose: Authenticated web interface for manual data updates
- Location: `web/admin/` (to be implemented)
- Contains: Hours editor, override manager, parser status dashboard
- Depends on: API layer (admin endpoints)
- Used by: Dining administrators (password-protected)

## Data Flow

**Menu Fetching:**

1. Client requests menu for hall + date
2. API checks Redis cache
3. If cached (TTL < 30 min), return cached data
4. If cache miss, run appropriate parser (Sodexo/BonAppetit/Pomona)
5. Parser scrapes vendor website, returns structured menu
6. Store in PostgreSQL `menus` table
7. Store in Redis cache (30-min TTL)
8. Return to client

**Crowding Aggregation:**

1. Mobile app detects location permission granted
2. App generates random session_id (rotated on each launch)
3. Every 30 seconds, app sends: `POST /api/v2/location {session_id, lat, lng, timestamp}`
4. Backend stores in Redis key `location:{session_id}` with 120-second TTL
5. Aggregation job runs every 30 seconds:
   - Iterate all hall geofences
   - Count unique session_ids within radius
   - Compare to thresholds (not busy < 15, moderate 15-40, busy > 40)
   - Store level in Redis `crowding:{hall_id}` (60-sec TTL)
6. Client requests `GET /api/v2/crowding` → returns snapshot
7. Session expires after 2 minutes of inactivity, or app closes

**Schedule-Based Fallback:**

When location data insufficient (count < minimum threshold):
- Calculate position within current meal window (0.0 = start, 1.0 = end)
- Apply triangle curve: peak at 0.5 (middle), zero at edges
- Map curve to three levels: > 0.6 = busy, > 0.3 = moderate, else = not busy
- Set `is_estimated: true` in crowding response

**State Management:**

Web/Mobile:
- React Query for server state (menu data, crowding levels)
- Local state (React hooks) for UI state (selected date, preferred college)
- AsyncStorage for offline cache of recently viewed menus

Backend:
- In-memory parser state (session objects, HTTP connections)
- Redis for transient state (location pings, crowding snapshots)
- PostgreSQL for persistent state (all business data)

## Key Abstractions

**DiningHall:**
- Purpose: Represent a single dining commons with identity, location, and metadata
- Examples: `backend/models/dining_hall.py` (to be created)
- Pattern: Data class with computed properties (is_open_now, get_current_meal)

**MenuParser:**
- Purpose: Abstract interface for vendor-specific menu scraping
- Examples: `backend/parsers/sodexo.py`, `backend/parsers/bonappetit.py`, `backend/parsers/pomona.py`
- Pattern: Base class with `parse(date) -> Menu` interface; subclasses implement vendor logic

**Menu:**
- Purpose: Organize menu items by station/category for a specific hall, date, meal
- Examples: Stored as JSONB in PostgreSQL, structured as `{stations: [{name, items: [{name, tags}]}]}`
- Pattern: Immutable data structure, server-generated once per day per hall per meal

**CrowdingLevel:**
- Purpose: Enum representing three-tier crowding state
- Examples: `NOT_BUSY`, `MODERATE`, `BUSY`
- Pattern: Enum with thresholds applied at aggregation time

**HallHours:**
- Purpose: Operating hours for a dining hall, with day-of-week and special date overrides
- Examples: Base hours in `dining_hours` table; overrides in `dining_hours_overrides`
- Pattern: Composite query (merge base schedule + check for overrides on given date)

## Entry Points

**Backend API:**
- Location: `backend/main.py` (FastAPI app)
- Triggers: Web requests to `/api/v2/*` routes
- Responsibilities: Route requests, validate inputs, call business logic, serialize responses

**Web Frontend:**
- Location: `web/app/page.tsx` (Next.js App Router entry)
- Triggers: Browser load of domain
- Responsibilities: Render hall list, fetch initial menu/crowding data, initialize React Query

**Mobile App:**
- Location: `mobile/app/index.tsx` (Expo Router entry)
- Triggers: App launch on iOS/Android device
- Responsibilities: Generate session_id, request location permission, render hall list

**Menu Parser Scheduler:**
- Location: Background job (to be determined: scheduled task, message queue, or on-demand)
- Triggers: Cache miss on menu request, or periodic refresh (not implemented in v1)
- Responsibilities: Run parser, store result, handle errors gracefully

**Admin Panel:**
- Location: `web/admin/layout.tsx` (password-protected Next.js route)
- Triggers: Admin navigates to `/admin`
- Responsibilities: Authenticate user, provide UI for hours/overrides editing

## Error Handling

**Strategy:** Graceful degradation with fallback to schedule-based estimates

**Patterns:**

- **Parser failure**: Cache miss triggers parser → parser fails → return cached stale data if available, else return `is_estimated: true` with schedule-based menu
- **Location service unavailable**: Continue without location data, show estimated crowding
- **Database connection error**: Return cached data if available, else 503 Service Unavailable
- **API rate limit**: Reject with 429, client should retry with exponential backoff
- **Invalid coordinates**: Reject `POST /location` with 400 Bad Request, validate against Claremont area bounding box

All errors logged server-side for monitoring; clients gracefully handle missing data.

## Cross-Cutting Concerns

**Logging:**
- Backend: Python logging module, structured logs for parser runs and API requests
- Frontend: console.log for development; error tracking with external service (not yet configured)

**Validation:**
- Backend: Pydantic models for request/response validation (FastAPI built-in)
- Frontend: TypeScript for type safety; React Query for data validation

**Authentication:**
- Public endpoints: No authentication (menu, crowding data available to all)
- Admin endpoints: Single password via HTTP Basic Auth or JWT token
- Location endpoint: Rate-limited by session_id (no auth required, session-based tracking)

**CORS:**
- Backend allows requests from configured frontend origins (Vercel domain, localhost:3000)
- Mobile app: Direct HTTPS requests (no CORS needed)

---

*Architecture analysis: 2026-02-07*
