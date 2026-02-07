# External Integrations

**Analysis Date:** 2026-02-07

## APIs & External Services

**Menu Data Providers:**
- **Sodexo** - Web scraping for Harvey Mudd Hoch-Shanahan dining hall menus
  - Parser implementation: `SodexoParser` Python class
  - Data source: Sodexo website scraping (no official API documented)
  - Auth: None required (public website scraping)

- **Bon Appétit** - Web scraping for CMC Collins, Scripps Malott, Pitzer McConnell menus
  - Parser implementation: `BonAppetitParser` Python class
  - Data source: Bon Appétit website scraping (no official API documented)
  - Auth: None required (public website scraping)

- **Pomona Dining** - Web scraping for Pomona Frank, Frary, Oldenborg menus
  - Parser implementation: `PomonaParser` Python class
  - Data source: Pomona College dining website (no official API documented)
  - Auth: None required (public website scraping)

## Data Storage

**Databases:**
- PostgreSQL (managed via Railway)
  - Connection: Environment variable (DATABASE_URL)
  - Tables: dining_halls, dining_hours, dining_hours_overrides, menus
  - Client: psycopg2 or asyncpg (async)
  - Schema: Defined in PRD with dining hall master data, hours, and menu JSONB storage

**Cache:**
- Redis (managed via Railway or external service)
  - Connection: Environment variable (REDIS_URL)
  - Purpose: Menu caching (30-minute TTL), location session storage (2-minute TTL), crowding aggregation snapshots (60-second TTL)
  - Key patterns:
    - `location:{session_id}` - Ephemeral location pings from mobile app
    - `crowding:{hall_id}` - Aggregated crowding levels with count and timestamp
    - Menu cache keys (unspecified format, likely hash of hall_id + date + meal)

**File Storage:**
- Not used - All data stored in PostgreSQL or Redis

## Authentication & Identity

**Admin Panel Auth:**
- Simple password authentication (no OAuth required for v1)
- Single admin account sufficient
- Protection: Basic auth or session-based authentication
- Endpoints: `/api/v2/admin/*` routes protected

**User Authentication:**
- Fully anonymous - No user accounts required
- Session tracking: Random UUID generated per app launch (not persisted)
- Location sharing is opt-in via mobile platform permission requests

## Monitoring & Observability

**Error Tracking:**
- Not specified in PRD - to be determined

**Logs:**
- Not specified in PRD - Standard application logging expected
- Parser status dashboard planned for admin panel showing last successful fetch times

**Health Monitoring:**
- Parser uptime target: 95%+ successful menu fetches
- Failure handling: Web scraper failures are acceptable initially; failures will be noticeable to users

## CI/CD & Deployment

**Hosting:**
- **Backend:** Railway managed platform (FastAPI service)
- **Frontend (Web):** Vercel (Next.js 14 deployment)
- **Frontend (Mobile):** Expo EAS Build for iOS App Store and Google Play Store
- **Databases:** Railway managed PostgreSQL
- **Cache:** Railway managed Redis or external Redis provider

**CI Pipeline:**
- Not specified in PRD - Likely configured via Vercel GitHub integration for web
- Mobile builds via Expo EAS (managed build service)
- Backend deployments via Railway GitHub integration

## Environment Configuration

**Required env vars (Backend):**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ADMIN_PASSWORD` - Simple admin auth credential
- `API_HOST` - Backend API domain (for CORS configuration)

**Required env vars (Frontend Web):**
- `NEXT_PUBLIC_API_URL` - Backend API endpoint URL

**Required env vars (Mobile):**
- `API_URL` - Backend API endpoint URL (configured in app.json or via Expo environment)

**Secrets location:**
- Environment variables managed by:
  - Railway for backend (via dashboard or .env file in project, never committed)
  - Vercel for web frontend (via dashboard environment variables)
  - Expo Secrets for mobile app (via Expo dashboard)

## Webhooks & Callbacks

**Incoming:**
- None specified - API is request/response based

**Outgoing:**
- None specified - No external service callbacks

## Location Services Integration

**Mobile Platform:**
- **iOS:** `expo-location` with "When In Use" permission only (foreground-only location access)
- **Android:** `expo-location` with `ACCESS_FINE_LOCATION` permission and foreground service type

**Backend Location Endpoint:**
- `POST /api/v2/location` - Receives anonymous location pings
- Input: `{ session_id, lat, lng, timestamp }`
- Rate limiting: Maximum 2 requests per minute per session_id
- Validation: Coordinates must fall within Claremont area bounding box

**Geofence Processing:**
- Server-side geofence calculation using hall coordinates and 50m radius
- Aggregation job runs every 30 seconds to count unique sessions per geofence
- Schedule-based fallback when insufficient location data available

---

*Integration audit: 2026-02-07*
