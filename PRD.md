# Product Requirements Document: 5C Menu App v2

## Overview

A dining menu application for the Claremont Colleges (Harvey Mudd, CMC, Scripps, Pitzer, Pomona) with real-time crowding indicators based on anonymous location data.

### Goals
- Provide students with daily dining hall menus across all 5C dining halls
- Show real-time crowding levels (Busy / Moderate / Not Busy) for each hall
- Support web and mobile (iOS/Android) with a shared codebase
- Maintain user privacy — no accounts, fully anonymous

### Non-Goals (Future Phases)
- Advertising / monetization system
- Semantic search over menus (ChromaDB)
- Estimated wait times in minutes
- Push notifications

---

## Target Users

**Primary**: Claremont Colleges students deciding where to eat

**User needs**:
- "What's being served at Hoch today?"
- "Is Collins busy right now?"
- "What are the hours for dinner at Frary?"
- "What's open right now?"

---

## Platforms

| Platform | Technology | Notes |
|----------|------------|-------|
| Web | React (Next.js) | Responsive, works on desktop and mobile browsers |
| iOS | Expo (React Native) | Native app with location permissions |
| Android | Expo (React Native) | Native app with location permissions |

Expo allows a single React Native codebase for iOS/Android with managed location APIs and OTA updates.

---

## Features

### 1. Menu Display

**Description**: Show dining hall menus organized by meal (breakfast, lunch, dinner, late night).

**Requirements**:
- Display menus for all 7 dining halls:
  - Harvey Mudd: Hoch-Shanahan
  - CMC: Collins
  - Scripps: Malott
  - Pitzer: McConnell
  - Pomona: Frank, Frary, Oldenborg
- Group menu items by station (Grill, Vegan, Main Plate, etc.)
- Show item names with dietary tags (vegan, vegetarian, gluten-free) where available
- Show meal hours for each dining hall (fetched from database, not hardcoded)
- Support date navigation (today, tomorrow, specific date)
- Pull-to-refresh for latest data
- Offline caching of recently viewed menus

**Explicitly NOT showing**:
- Full nutritional information (available on dining hall websites)

**Data sources**:
- Sodexo API/website (Hoch)
- Bon Appétit API/website (Collins, Malott, McConnell)
- Pomona dining website (Frank, Frary, Oldenborg)

### 2. Crowding Indicators

**Description**: Show real-time busyness levels for each dining hall based on anonymous location data.

**Requirements**:
- Three-level indicator: **Busy** / **Moderate** / **Not Busy**
- Displayed as a badge next to dining hall name (not color-coded — halls already have school colors)
- Update in near real-time (30-60 second lag acceptable)
- Show indicator on main hall list and individual hall views

**Location Permission Flow**:
1. On first app launch, prompt for location permission
2. If user denies, they can still browse menus but cannot see crowding data
3. If user later tries to view crowding, re-prompt with explanation
4. **You must contribute location to see crowding** — no free riders

**Privacy requirements**:
- Fully anonymous — no user accounts required
- Location only collected while app is in foreground (app open and active)
- No persistent device identifiers stored server-side
- Session IDs rotate on each app launch

**Insufficient data handling**:
- When not enough users are sharing location, fall back to schedule-based estimate
- Show disclaimer: "Estimated based on typical patterns"
- Schedule heuristic: Rush hour = middle of meal window (e.g., 12pm for 11am-1pm lunch, 6pm for 5pm-7pm dinner)

**Contribution visibility**:
- Show users they're helping: "You're helping 47 other students see how busy it is"

**Thresholds** (tunable):
| Level | Definition |
|-------|------------|
| Not Busy | < 15 active sessions in geofence |
| Moderate | 15-40 active sessions |
| Busy | > 40 active sessions |

*Note: Thresholds will need calibration based on real usage data.*

**Future enhancement** (not v1):
- Mr. Incredible meme progression for crowding levels (increasingly cursed images as it gets busier)

### 3. Home Screen / Hall List

**Default view when opening app**:
- List of all dining halls
- Each hall shows: name, school color, current hours, crowding badge
- **"What's Open Now" section** at top showing only halls currently serving

**Navigation**:
- Tap a hall → opens detail view with meals, times, menu items
- Halls organized by school, user can set preferred school to sort first
- Last viewed hall is NOT persisted (keep it simple)

### 4. Settings

**Requirements**:
- Toggle location sharing on/off
- Set preferred college (affects default sort order)
- Dark mode support (follow system default)
- About / privacy policy link

### 5. Admin Panel (Web Only)

**Description**: Simple web interface for manual updates to dining hall data.

**Requirements**:
- Password-protected access (single admin account is fine)
- Edit dining hall hours by day of week
- Edit special hours (holidays, breaks)
- Changes take effect immediately (no app update required)
- View parser status (last successful fetch time per hall)

**Why this matters**: Storing hours in the database (not hardcoded in app) means you can update hours during Thanksgiving break without waiting for App Store review.

---

## Technical Architecture

### Backend

| Component | Technology |
|-----------|------------|
| Framework | Python + FastAPI |
| Database | PostgreSQL |
| Cache | Redis (for crowding aggregation + menu caching) |
| Hosting | Railway |

**API Endpoints**:

```
GET  /api/v2/halls
     → Returns list of dining halls with hours and current crowding levels

GET  /api/v2/menus?hall={hall}&date={YYYY-MM-DD}
     → Returns menu for specified hall and date

GET  /api/v2/crowding
     → Returns crowding levels for all halls

POST /api/v2/location
     Body: { session_id, lat, lng, timestamp }
     → Receives anonymous location ping

GET  /api/v2/open-now
     → Returns halls currently open with crowding

--- Admin endpoints (authenticated) ---

GET  /api/v2/admin/halls
POST /api/v2/admin/halls/{hall}/hours
     → Update hours for a hall
```

**Caching Strategy** (matching current system):
- Menus cached in Redis with 30-minute TTL
- Timestamps rounded to 30-minute intervals for cache key efficiency
- No scheduled jobs — fetch on demand, cache the result
- Parser runs on cache miss, result cached for subsequent requests

**Menu Parsers** (Python):
- `SodexoParser` — scrapes Hoch menu
- `BonAppetitParser` — scrapes Collins, Malott, McConnell
- `PomonaParser` — scrapes Frank, Frary, Oldenborg

### Frontend (Web)

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| State | React Query (TanStack Query) |
| Hosting | Vercel |

### Mobile (iOS/Android)

| Component | Technology |
|-----------|------------|
| Framework | Expo (React Native) |
| Navigation | Expo Router |
| Location | expo-location (foreground only) |
| State | React Query |
| Offline | AsyncStorage for menu cache |

### Offline Support

- Cache last-fetched menus in local storage (AsyncStorage on mobile, localStorage on web)
- When offline, show cached menus with "Last updated X hours ago" indicator
- Crowding data not available offline (requires network)

---

## Crowding System Design

### Data Flow

```
┌─────────────────┐     POST /location      ┌─────────────────┐
│   Mobile App    │ ───────────────────────→│   FastAPI       │
│ (foreground)    │    {session_id,         │   Backend       │
│                 │     lat, lng}           │                 │
└─────────────────┘                         └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │     Redis       │
                                            │  (session store)│
                                            │                 │
                                            │ session_id →    │
                                            │   {lat,lng,ts}  │
                                            │   TTL: 2 min    │
                                            └────────┬────────┘
                                                     │
                                            ┌────────▼────────┐
                                            │ Aggregation Job │
                                            │ (every 30 sec)  │
                                            │                 │
                                            │ Count sessions  │
                                            │ per geofence    │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
        GET /crowding                       │   Crowding      │
    ←───────────────────────────────────────│   Levels        │
        {hoch: "busy", ...}                 │   (in Redis)    │
                                            └─────────────────┘
```

### Session Lifecycle

1. App opens → generate random UUID as `session_id` (not persisted across launches)
2. User grants location permission → start sending pings every 30 seconds
3. Each ping: `POST /location` with `{session_id, lat, lng, timestamp}`
4. Backend stores in Redis with 2-minute TTL
5. Aggregation job counts unique session_ids within each hall's geofence radius
6. App closes → pings stop → session expires from Redis after 2 minutes
7. App reopens → new session_id generated → cycle repeats

### Schedule-Based Fallback

When insufficient location data is available:

```python
def estimate_crowding(hall: str, current_time: datetime) -> str:
    """Estimate crowding based on time within meal window."""
    meal = get_current_meal(hall, current_time)
    if not meal:
        return "not_busy"  # Hall is closed

    # Calculate position within meal window (0.0 to 1.0)
    meal_start = meal.start_time
    meal_end = meal.end_time
    meal_duration = (meal_end - meal_start).total_seconds()
    time_into_meal = (current_time - meal_start).total_seconds()
    position = time_into_meal / meal_duration

    # Peak is at middle of meal (position = 0.5)
    # Using a simple triangle: peaks at 0.5, zero at 0 and 1
    peak_factor = 1 - abs(position - 0.5) * 2

    if peak_factor > 0.6:
        return "busy"
    elif peak_factor > 0.3:
        return "moderate"
    else:
        return "not_busy"
```

### Geofence Definitions

| Hall | Latitude | Longitude | Radius (m) |
|------|----------|-----------|------------|
| Hoch | 34.1061 | -117.7117 | 50 |
| Collins | 34.1012 | -117.7089 | 50 |
| Malott | 34.1044 | -117.7106 | 50 |
| McConnell | 34.1037 | -117.7148 | 50 |
| Frank | 34.0975 | -117.7131 | 50 |
| Frary | 34.0970 | -117.7117 | 50 |
| Oldenborg | 34.0985 | -117.7100 | 50 |

*Note: Coordinates are approximate. Verify with actual GPS readings on-site. Radius may need adjustment — 50m is a starting point.*

---

## Data Models

### Dining Hall (Postgres)

```sql
CREATE TABLE dining_halls (
    id VARCHAR(20) PRIMARY KEY,       -- 'hoch', 'collins', etc.
    name VARCHAR(100) NOT NULL,       -- 'Hoch-Shanahan Dining Commons'
    college VARCHAR(20) NOT NULL,     -- 'mudd', 'cmc', 'scripps', 'pitzer', 'pomona'
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    geofence_radius_m INTEGER DEFAULT 50,
    color VARCHAR(7),                 -- '#FFA500' (school color hex)
    parser_type VARCHAR(20)           -- 'sodexo', 'bonappetit', 'pomona'
);

CREATE TABLE dining_hours (
    id SERIAL PRIMARY KEY,
    hall_id VARCHAR(20) REFERENCES dining_halls(id),
    day_of_week INTEGER NOT NULL,     -- 0=Sunday, 6=Saturday
    meal VARCHAR(20) NOT NULL,        -- 'breakfast', 'lunch', 'dinner', 'latenight'
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(hall_id, day_of_week, meal)
);

CREATE TABLE dining_hours_overrides (
    id SERIAL PRIMARY KEY,
    hall_id VARCHAR(20) REFERENCES dining_halls(id),
    date DATE NOT NULL,
    meal VARCHAR(20),                 -- NULL means entire day
    start_time TIME,                  -- NULL means closed
    end_time TIME,
    reason VARCHAR(200),              -- 'Thanksgiving Break'
    UNIQUE(hall_id, date, meal)
);
```

### Menu (Postgres)

```sql
CREATE TABLE menus (
    id SERIAL PRIMARY KEY,
    hall_id VARCHAR(20) REFERENCES dining_halls(id),
    date DATE NOT NULL,
    meal VARCHAR(20) NOT NULL,
    stations JSONB NOT NULL,          -- [{name, items: [{name, tags}]}]
    fetched_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(hall_id, date, meal)
);
```

### Location Ping (Redis only — ephemeral)

```
Key: location:{session_id}
Value: {lat, lng, hall, timestamp}
TTL: 120 seconds
```

### Crowding Snapshot (Redis)

```
Key: crowding:{hall_id}
Value: {
    level: "busy" | "moderate" | "not_busy",
    count: 47,
    is_estimated: false,
    updated_at: "2024-01-15T12:30:00Z"
}
TTL: 60 seconds
```

---

## Privacy & Security

### Location Data
- No persistent storage of location pings beyond 2-minute Redis TTL
- Session IDs are random UUIDs, regenerated each app launch, not tied to device or user
- No analytics or logging of individual location data
- Aggregated counts only (never raw coordinates) stored in any persistent form

### API Security
- Rate limiting on `/location` endpoint (max 2 req/min per session_id)
- Input validation on coordinates (must be within Claremont area bounding box)
- HTTPS only
- Admin endpoints protected by password authentication

### Permissions
- iOS: Request "When In Use" location (not "Always")
- Android: Request `ACCESS_FINE_LOCATION` with foreground service type

---

## Alternative Approaches for Crowding (Future Consideration)

If GPS-based tracking proves insufficient (low adoption, accuracy issues):

### Option A: Self-Reported Crowding
- Users tap "How busy is it?" when at a dining hall
- Options: Empty / Moderate / Packed
- Pros: No location permissions needed, works on web
- Cons: Requires active user participation

### Option B: Campus Wi-Fi Partnership
- Partner with 5C IT to get anonymized device counts per building
- Pros: Highly accurate, no user opt-in required
- Cons: Requires institutional partnership, may have policy hurdles

### Option C: Hybrid Approach
- Use schedule heuristics as baseline
- Overlay with GPS data when available
- Supplement with self-reported data
- Gracefully degrade when data is sparse

---

## Milestones

### Phase 1: Core Menu App (Web)
- [ ] FastAPI backend scaffold
- [ ] PostgreSQL schema (halls, hours, menus)
- [ ] Menu parsers in Python (Sodexo, Bon Appétit, Pomona)
- [ ] Redis caching layer
- [ ] API endpoints: `/halls`, `/menus`, `/open-now`
- [ ] Next.js frontend with menu display
- [ ] Hall list with "What's Open Now" section
- [ ] Date navigation and hall switching
- [ ] Dark mode support
- [ ] Deploy to Railway (backend) + Vercel (frontend)

### Phase 2: Admin Panel
- [ ] Admin authentication
- [ ] Hours editing UI
- [ ] Hours override for special dates
- [ ] Parser status dashboard

### Phase 3: Mobile App
- [ ] Expo project setup
- [ ] Menu display screens (port from web)
- [ ] Navigation and settings
- [ ] Offline caching with AsyncStorage
- [ ] Build and deploy to TestFlight / Play Store internal testing

### Phase 4: Crowding Feature
- [ ] Redis integration for session storage
- [ ] Location ping endpoint with rate limiting
- [ ] Aggregation job and geofence logic
- [ ] Schedule-based fallback estimator
- [ ] Crowding badges in UI (web + mobile)
- [ ] Location permission flow in mobile app
- [ ] "Helping X students" contribution indicator

### Phase 5: Polish & Launch
- [ ] Threshold calibration with real data
- [ ] Error handling and edge cases
- [ ] Performance optimization
- [ ] App Store / Play Store submission (crowding as prominent feature)
- [ ] Public launch via Fizz announcement

---

## Open Questions

1. **Coordinate verification**: Need to verify dining hall GPS coordinates on-site before launch.

2. **Threshold calibration**: Initial thresholds (15/40) are guesses. Need real usage data to tune.

3. **Geofence overlap**: Frank and Frary are close together (~50m apart). May need smaller radii or hall-specific tuning.

4. **Minimum viable sample**: Estimate ~50+ concurrent campus-wide users needed for reliable crowding. May need to rely heavily on schedule-based estimates initially.

5. **Parser brittleness**: Vendor websites change occasionally. Current approach (no alerting) is acceptable for now — failures will be noticeable. May add monitoring later.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Daily active users (DAU) | 500+ within first semester |
| Location opt-in rate | 40%+ of mobile users |
| Crowding data availability | 80%+ of peak meal times have GPS-based data |
| Parser uptime | 95%+ successful menu fetches |
| App Store rating | 4.5+ stars |

---

## Appendix: Dining Hall Reference

| Hall | College | Food Service | Typical Meals |
|------|---------|--------------|---------------|
| Hoch-Shanahan | Harvey Mudd | Sodexo | Breakfast, Lunch, Dinner |
| Collins | CMC | Bon Appétit | Breakfast, Lunch, Dinner, Late Night |
| Malott | Scripps | Bon Appétit | Breakfast, Lunch, Dinner |
| McConnell | Pitzer | Bon Appétit | Breakfast, Lunch, Dinner |
| Frank | Pomona | Pomona Dining | Breakfast, Lunch, Dinner |
| Frary | Pomona | Pomona Dining | Breakfast, Lunch, Dinner |
| Oldenborg | Pomona | Pomona Dining | Lunch only (language tables) |
