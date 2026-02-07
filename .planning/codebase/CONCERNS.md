# Codebase Concerns

**Analysis Date:** 2026-02-07

## Project Status

This is an early-stage project with **no production source code yet**. Concerns below identify risks and issues that should be addressed during initial implementation phases.

---

## Tech Debt & Architectural Concerns

### Location Privacy Implementation Risk

**Issue:** Crowding system requires precise balance between utility and privacy compliance.

**Files:** Will impact backend location endpoint `/api/v2/location` and mobile location tracking (Expo)

**Concerns:**
- Session ID rotation relies on app restart; no logout/pause mechanism means foreground tracking is only guarantee
- 2-minute Redis TTL on location pings is tight; clock skew or network delays could cause premature expiration
- Geofence radius (50m) is small and overlapping (Frank/Frary ~50m apart per PRD line 488) — risk of misattribution or missing data near boundaries
- No mechanism documented to prevent location spoofing (users could send fake coordinates)

**Impact:** Privacy claims could be violated if sessions persist longer than 2 minutes or if pings are logged beyond Redis ephemeral storage.

**Fix approach:**
- Document explicit session lifecycle guarantees in code comments
- Implement session TTL monitoring with alerts if pings exceed TTL
- Add coordinate bounding box validation to reject out-of-Claremont coordinates
- Consider rate limiting per session_id to prevent spoofing bursts

---

### Parser Brittleness Without Monitoring

**Issue:** Menu parsing relies on web scraping for three vendor sites (Sodexo, Bon Appétit, Pomona).

**Files:** Backend will contain `SodexoParser`, `BonAppetitParser`, `PomonaParser` classes (location TBD)

**Concerns:**
- No alerting documented when parsers fail (PRD line 492: "failures will be noticeable")
- Vendor website HTML changes break parsers silently
- No fallback or graceful degradation if all three parsers fail simultaneously
- 30-minute cache TTL means parsing failures could leave users with stale data for half an hour
- No circuit breaker pattern to prevent repeated failed parse attempts

**Impact:** Users see outdated or missing menus during parser failures. No visibility into when failure occurred.

**Fix approach:**
- Implement parser error logging and monitoring dashboard (even simple: last_fetch_success timestamp per parser)
- Add try-catch around all CSS selector queries with specific error messages
- Implement circuit breaker: if parse fails 3x in a row, fall back to cached data and alert admin
- Document expected HTML structure for each vendor with version info

---

### Crowding Estimation Accuracy Concerns

**Issue:** Schedule-based crowding fallback (PRD lines 276-300) makes assumptions about meal patterns.

**Files:** Backend crowding estimation logic

**Concerns:**
- Triangle heuristic assumes symmetric peak at meal midpoint; real dining patterns vary (lunch peak at 12:30, not 12:00)
- No calibration thresholds documented (peak_factor > 0.6 = "busy" is arbitrary)
- Thresholds from PRD (15/40 active sessions) are acknowledged guesses needing calibration (line 110, 486)
- Assumes sufficient location contributor density (~50+ concurrent users per PRD line 490); may be unrealistic initially
- Fall-forward mechanism: if GPS data insufficient, app shows estimated crowding without disclaimer option explored

**Impact:** Users receive inaccurate crowding levels during low-adoption periods or peak times. Over-reliance on wrong heuristics could undermine feature credibility.

**Fix approach:**
- Make crowding thresholds and peak_factor constants configurable per hall (not hardcoded)
- Implement telemetry to track: actual vs. estimated crowding, contributor count per time window
- Add explicit "insufficient data" state with disclaimer (don't just guess)
- Document initial 4-week calibration period with admin review process

---

## Security Considerations

### Admin Authentication Gap

**Issue:** Admin panel mentioned (PRD lines 136-146) but no auth mechanism specified.

**Files:** Backend admin endpoints `/api/v2/admin/halls/*`

**Concerns:**
- PRD says "single admin account is fine" (line 140) but no password hashing, session management, or MFA discussed
- No rate limiting or attempt limits specified for admin login
- No audit log for who changed what/when
- Admin endpoints could be brute-forced without protection

**Impact:** Unauthorized access to admin panel allows arbitrary menu/hours changes, breaking user experience.

**Fix approach:**
- Implement bcrypt password hashing (never plain text)
- Add exponential backoff after 3 failed login attempts
- Use JWT tokens with 1-hour expiry for admin sessions
- Log all admin changes with timestamp and IP address
- Consider adding CORS/IP whitelist for admin endpoints

---

### Rate Limiting on Location Endpoint

**Issue:** Location endpoint rate limiting mentioned (PRD line 403) but not specified.

**Files:** Backend `/api/v2/location` endpoint

**Concerns:**
- PRD says "max 2 req/min per session_id" (line 403) but no implementation guidance
- No mention of what happens when limit exceeded (reject? queue? backoff?)
- No per-IP rate limiting (users could create multiple session_ids)
- Location endpoint should be unauthenticated but needs DDoS protection

**Impact:** Attackers could spam location pings to artificially inflate crowding numbers or cause Redis memory exhaustion.

**Fix approach:**
- Implement rate limiter: 2 requests per 60 seconds per session_id (hard limit)
- Add IP-based limit: max 100 requests per minute per IP (generous for dense campus areas)
- Return 429 (Too Many Requests) when limit exceeded
- Monitor Redis memory usage; implement automatic session eviction if >80% full

---

## Data Model Concerns

### Geofence Accuracy Unverified

**Issue:** GPS coordinates and radii in PRD (lines 304-314) are marked as "approximate."

**Files:** PostgreSQL `dining_halls` table (latitude, longitude, geofence_radius_m)

**Concerns:**
- Coordinates not field-verified; error of 30-50m could cause incorrect hall attribution
- 50m radius is tight given Claremont campus density; geofences may overlap
- Frank and Frary are ~50m apart (line 488); geofences will definitely overlap
- No versioning/history of coordinate changes; can't compare crowding before/after coordinate update

**Impact:** Users at Frank/Frary boundary could be misattributed, breaking crowding accuracy. GPS drift over time goes undetected.

**Fix approach:**
- Before launch: field-verify all 7 coordinates with GPS receiver or Google Maps verification
- Document expected accuracy (±10m minimum)
- Store coordinate verification date and confidence score
- Implement per-hall geofence overlap detection and smaller overlap radius fallback
- Consider moving to mapping service API (Google Maps API) instead of hardcoded coordinates

---

## Performance Bottlenecks

### Redis Aggregation Job Scalability

**Issue:** Crowding aggregation job runs "every 30 seconds" (PRD line 248) counting sessions per geofence.

**Files:** Backend aggregation job (location/scheduler service)

**Concerns:**
- No mention of pagination or batch processing for large session counts
- Geofence distance calculation in Redis could be slow with thousands of sessions
- If 7 halls × 30-second interval × Python distance calculations, could cause latency spikes
- No caching of aggregation results; clients could hit Redis multiple times per second

**Impact:** High latency on crowding API responses. Aggregation job could block other Redis operations during peak times.

**Fix approach:**
- Use Redis geospatial indexes (`GEOADD`, `GEORADIUS`) instead of manual distance calculation
- Pre-aggregate results and cache in Redis with 30-second TTL (read-only for clients)
- Monitor aggregation job execution time; alert if >5 seconds
- Profile with realistic 1000+ session load before launch

---

### Menu Parser Caching Strategy

**Issue:** Menu caching uses 30-minute TTL (PRD line 188-189) with "no scheduled jobs" refresh.

**Files:** Redis menu cache, backend `/api/v2/menus` endpoint

**Concerns:**
- Cache misses at 30+ min mark trigger synchronous parser run; blocks API response
- Parser fetch could take 5-30 seconds (web scraping); users get slow response
- No cache warming; all three dining halls hit at same time on cache expiry = stampede
- Menu updates from vendor are unpredictable; 30 min is arbitrary (could miss lunch menu updates)

**Impact:** Slow API responses during cache misses. Menu staleness risk if vendor updates mid-cache window.

**Fix approach:**
- Implement cache warming: background job fetches menu at +25min before expiry
- Add "last-modified" header from vendor; compare before re-parsing
- Consider shorter TTL for menus within 1 hour of meal times, longer outside
- Return stale cache with "Cached X minutes ago" header if parse fails, instead of blocking

---

## Missing Critical Features

### No Offline Menu Data Specification

**Issue:** PRD mentions offline caching (lines 217-221) but data model not defined.

**Files:** Mobile app AsyncStorage, web app localStorage

**Concerns:**
- No schema specified for offline menu storage
- No sync strategy documented: how does app reconcile stale offline data with fresh server data?
- No versioning: how does app know when offline data is >2 hours old?
- Web localStorage size limits (~5MB); storing 7 halls × 30 days of menus could exceed limit

**Impact:** Mobile/web offline functionality could crash or show corrupted menus.

**Fix approach:**
- Define offline storage schema: `{ hall_id, date, meal, menu_data, cached_at, ttl_seconds }`
- Implement "age check" on app open: discard offline data >24 hours old
- Add storage quota management: cap total offline data to 3MB, LRU eviction by last_accessed
- Show "Offline - Last updated 3 hours ago" disclaimer when serving stale data

---

### Missing Dark Mode Implementation Details

**Issue:** PRD says "Dark mode support (follow system default)" (line 131) but no approach specified.

**Files:** Web Next.js app, mobile Expo app

**Concerns:**
- No CSS strategy specified: Tailwind dark: variants? CSS-in-JS? System color overrides?
- No testing strategy for color contrast in dark mode (accessibility risk)
- No mention of dark mode for images (school colors might not be readable on dark backgrounds)
- Mobile Expo doesn't have built-in dark mode system observer; requires expo-system-ui or custom solution

**Impact:** Dark mode could have illegible text or broken layouts. Accessibility violations could block app store submissions.

**Fix approach:**
- Use Tailwind `dark:` variant classes exclusively (consistent across web/mobile)
- Run accessibility audit in dark mode: minimum WCAG AA contrast (4.5:1)
- For school color badges in dark mode, add 80% opacity white overlay instead of changing color
- Mobile: use `expo-system-ui` for system dark mode detection, test on both iOS and Android

---

## Test Coverage Gaps

### No Test Plan for Parsers

**Issue:** Menu parsers (Sodexo, Bon Appétit, Pomona) mentioned but no testing strategy documented.

**Files:** Backend parser modules

**Concerns:**
- No mock data specified for vendor websites
- No test for handling vendor HTML structure changes
- No test for malformed menu data (missing fields, empty stations)
- Parser integration tests likely require network calls; slow and brittle

**Impact:** Parser failures go undetected until prod; users see missing menus.

**Fix approach:**
- Store representative HTML snapshot from each vendor in `tests/fixtures/` directory
- Unit tests parse fixtures with known output
- Add integration tests with retry logic: 3 attempts over 30 seconds before timing out
- Document how to update fixtures when vendor HTML changes (with date/version tag)

---

### No Crowding Accuracy Testing

**Issue:** Crowding aggregation logic (geofences, thresholds) has no test plan.

**Files:** Backend crowding aggregation job

**Concerns:**
- No synthetic test data for overlapping geofences
- No tests for edge cases: coordinates exactly at boundary, multiple halls detected, none detected
- No tests for session TTL behavior: do sessions truly expire at 2 min?
- Aggregation job is background task; easy to break silently

**Impact:** Crowding reports are unreliable; users at boundaries see inconsistent levels.

**Fix approach:**
- Generate test dataset with 100+ synthetic location pings at known positions
- Test each geofence independently and overlapping scenarios
- Test TTL expiration: insert session, verify present at +59sec, absent at +121sec
- Add integration test that runs aggregation job and verifies output in <1 second

---

### Location Privacy Testing

**Issue:** Privacy guarantees (no persistent device ID, session rotation) need verification.

**Files:** Mobile app location tracking, backend session storage

**Concerns:**
- No test verifies session ID is actually new on app restart
- No test verifies location pings are actually deleted after 2 minutes
- No test verifies coordinates are validated for Claremont bounding box
- Mobile app could be logging locations to persistent storage without code review catching it

**Impact:** Privacy violations go undetected; could leak user location even after session ends.

**Fix approach:**
- Automated test: launch app, generate session_id, capture value, kill app, relaunch, verify new session_id generated
- Redis integration test: insert location ping, wait 3 min, verify deleted
- Coordinate validation test: reject pings outside Claremont box (±0.1 degrees), accept those inside
- Code review checklist: verify no location persisted to device filesystem or shared preferences

---

## Scaling Limits

### Redis Concurrent Session Capacity

**Issue:** Crowding system depends on Redis storing session pings with 2-min TTL.

**Files:** Backend Redis integration

**Concerns:**
- PRD estimates ~50+ concurrent users needed for reliable crowding (line 490); actual campus population 5000+
- At 40% location opt-in rate = 2000 potential users; even 5% active = 100 concurrent = 100 Redis keys every 30 sec
- Redis can handle this easily, but no capacity monitoring specified
- No sharding or cluster strategy if load exceeds single Redis instance

**Impact:** Redis memory exhaustion under peak load. Crowding becomes unavailable during lunch rush.

**Fix approach:**
- Monitor Redis memory usage; alert at 70% and 90%
- Set Redis `maxmemory-policy` to `allkeys-lru` (evict least-recently-used if full)
- Performance test: simulate 500 concurrent location pings, measure latency and memory
- Document Redis instance size requirements: start with 256MB, monitor first semester

---

### Database Query Performance for Menus

**Issue:** `/api/v2/menus` endpoint queries PostgreSQL for menu by hall and date.

**Files:** Backend menu query logic, PostgreSQL schema

**Concerns:**
- No index strategy specified on `dining_halls(id, date, meal)`
- Large JSONB `stations` column not analyzed for query impact
- No mention of pagination for date range queries (e.g., "get menus for next 7 days")
- No query plan or EXPLAIN output documented

**Impact:** Menu queries slow as database grows. Week-long menu queries could take seconds.

**Fix approach:**
- Add composite index: `CREATE INDEX idx_menus_hall_date ON menus(hall_id, date, meal)`
- Use EXPLAIN ANALYZE on all menu queries in test environment
- Limit date range queries to max 14 days; require explicit date for longer ranges
- Monitor slow query log; set threshold to 100ms (development) or 500ms (production)

---

## Known Assumptions at Risk

### GPS Accuracy Assumption

**Issue:** Geofencing assumes GPS accuracy within 50m; campus terrain may have dead zones.

**Files:** Mobile location tracking, backend geofence validation

**Concerns:**
- Indoor dining halls have poor GPS signal (typical accuracy 20-50m outdoors, worse indoors)
- Users could be inside Hoch but GPS shows them 30m away (different floor? adjacent building?)
- No fallback if GPS accuracy estimate is high (>30m error)
- Claremont campus has significant elevation variation and buildings could shadow signals

**Impact:** Users may not be counted for crowding even when inside dining hall.

**Fix approach:**
- Document GPS accuracy expectations; discard pings with >50m accuracy estimate
- Consider WiFi-based geofencing fallback (requires campus IT partnership, not viable for v1)
- Mobile app: show accuracy indicator to user; suppress crowding contribution if accuracy poor
- Test on-site in each dining hall at different times to measure actual accuracy

---

### Vendor API Stability

**Issue:** Scrapers depend on vendor website stability; no documented update plan.

**Files:** Parser modules (Sodexo, Bon Appétit, Pomona)

**Concerns:**
- Bon Appétit recently redesigned website; parsers may already be broken
- Pomona Dining runs custom website with unpredictable updates
- No version pinning or historical reference for what scrapers expect
- No communication channel with vendors; can't get advance notice of HTML changes

**Impact:** Menu parsing breaks without warning; potentially multi-day outages waiting for fix.

**Fix approach:**
- Before launch: verify all three parsers work against current vendor websites
- Quarterly check-in: test parsers against live sites, fix if needed
- Document vendor URLs and expected HTML structure (CSS selectors) with date
- Consider alternative: manually input menus if vendor APIs become available

---

## Dependencies at Risk

### Expo SDK Lock-In

**Issue:** Mobile app uses Expo (managed build service).

**Files:** Mobile app expo configuration, package.json

**Concerns:**
- Expo SDK updates sometimes break; can't use arbitrary native modules
- If Expo discontinues or prices increase, migration to React Native Bare difficult
- Geolocation via `expo-location` tied to Expo ecosystem
- Large apps with custom native code sometimes outgrow Expo

**Impact:** Vendor lock-in; expensive to migrate if requirements exceed Expo capabilities.

**Fix approach:**
- Start with Expo; monitor for limitations as app grows
- Document when to eject to Bare React Native (if feature gaps appear)
- Keep Expo SDK version pinned; test thoroughly before major version upgrades
- Budget for potential migration in year 2 if needed

---

### FastAPI Ecosystem Maturity

**Issue:** Backend uses FastAPI (relatively newer framework).

**Files:** Backend application structure

**Concerns:**
- Smaller ecosystem than Django/Flask; fewer third-party packages available
- Team expertise may vary; onboarding new developers requires FastAPI learning curve
- Long-term support commitment unclear compared to Django
- Async/await complexity could lead to subtle bugs if misused

**Impact:** Feature development could slow if FastAPI lacks required packages; need workarounds.

**Fix approach:**
- Evaluate at backend setup: is FastAPI well-suited for this project or should use Flask/Django?
- Document AsyncIO patterns; code review checklist includes async correctness
- Keep FastAPI pinned to well-tested LTS version until v2 is proven stable
- Plan quarterly dependency audit to catch security updates

---

## Development & Deployment Concerns

### Multi-Repo Coordination Risk

**Issue:** Project has separate backend, web, mobile codebases.

**Files:** `/backend`, `/web`, `/mobile` directories (currently placeholders)

**Concerns:**
- No shared versioning; frontend could expect API v2 while backend still on v1
- No documented deployment order (must backend deploy before web?)
- No E2E tests spanning multiple repos
- Monorepo alternative not explored; could simplify coordination

**Impact:** Deployments risk breaking integrations; coordination overhead as project grows.

**Fix approach:**
- Use semantic versioning for API; web/mobile pin to specific backend API version
- Document deployment checklist: backend first, then web/mobile
- Create E2E test suite in separate repo testing full flow
- Consider monorepo (yarn workspaces) if coordination overhead exceeds threshold

---

## Documentation Gaps

### No Admin Runbook

**Issue:** Admin panel for hours/overrides mentioned but no operation guide.

**Files:** Backend admin endpoints, planned admin UI (web)

**Concerns:**
- No documented process for: handling semester breaks, holiday hours, emergency closures
- No database schema documented for `dining_hours_overrides` queries
- No examples of common admin tasks (e.g., "Close dining hall for 2 hours due to event")
- Missing: who is admin? how are credentials managed?

**Impact:** Admin makes mistakes; wrong hours displayed to users during special periods.

**Fix approach:**
- Create `docs/admin-runbook.md` with step-by-step guides for common tasks
- Add form validation in admin UI to prevent overlapping overrides
- Require date range instead of open-ended overrides
- Add preview: "show users what they'll see" before saving hours

---

This analysis reflects the project's current early-stage status with significant implementation work ahead. Most concerns are forward-looking to inform initial development decisions.
