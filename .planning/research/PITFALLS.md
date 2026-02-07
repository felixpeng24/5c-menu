# Pitfalls Research

**Domain:** College dining hall menu app with web scraping, caching, and crowding features
**Researched:** 2026-02-07
**Confidence:** MEDIUM-HIGH (verified through multiple sources, prior art from similar 5C projects, and known production patterns)

## Critical Pitfalls

### Pitfall 1: Synchronous Scraping on Cache Miss Blocks API Responses

**What goes wrong:**
When the Redis cache TTL expires (30 minutes) and a user requests a menu, the API handler runs the parser synchronously before returning a response. Web scraping takes 2-30 seconds depending on vendor site responsiveness. The user stares at a spinner. Worse: if multiple users request the same hall simultaneously after TTL expiry, every request triggers a separate scrape of the same vendor page (cache stampede).

**Why it happens:**
The PRD explicitly states "no scheduled jobs -- fetch on demand, cache the result." This is architecturally simple but creates a direct coupling between user-facing latency and external site performance. Developers default to the simplest read-through cache pattern without considering that the "miss" path is catastrophically slow for scraping.

**How to avoid:**
1. Implement **stale-while-revalidate**: always return the most recent cached data immediately, then refresh in the background. Store a "soft TTL" (25 min) for triggering background refresh and a "hard TTL" (6 hours) for data expiry.
2. Implement **single-flight / request coalescing**: use a mutex or lock so only one scrape runs per hall+date+meal combo at a time. Other requests wait on the same result.
3. Add **TTL jitter**: randomize TTL between 25-35 minutes so all 7 halls don't expire simultaneously.
4. Persist menus in PostgreSQL on every successful scrape so there is always a fallback even if Redis is flushed.

**Warning signs:**
- API response times >3 seconds during meal transitions (breakfast-to-lunch)
- Spike in vendor site requests at exactly 30-minute intervals
- Multiple concurrent scrape tasks for the same hall in logs
- Users reporting blank menus or timeouts

**Phase to address:**
Phase 1 (Core Backend) -- this is foundational cache architecture. Getting this wrong means every subsequent feature inherits the latency problem.

---

### Pitfall 2: Parser Brittleness Without Structural Change Detection

**What goes wrong:**
Vendor websites (Sodexo, Bon Appetit, Pomona) change their HTML structure without notice. Parsers silently return empty menus, menus with missing stations, or crash entirely. The app shows "no menu available" for a dining hall that is actually serving food. Students stop trusting the app.

Prior art confirms this is not theoretical: the [RPI Sodexo menu scraper](https://github.com/JelloRanger/menu-scraper) broke when Sodexo changed formatting in 2014 and was abandoned. Bon Appetit previously had an unauthenticated legacy API that was shut off, forcing projects like the [Reed College menu app](https://github.com/Merlin04/reed-commons-menu) to switch to HTML scraping. The [Carleton Bon Appetit scraper](https://github.com/Machyne/pal/blob/master/api/bonapp/bon_api.py) uses regex to parse embedded `Bamco.menu_items` JavaScript objects from HTML -- an approach that breaks if Bon Appetit changes their client-side rendering.

**Why it happens:**
- Dining vendors redesign websites 1-2 times per academic year (semester transitions, vendor contract renewals)
- CSS selectors and XPath expressions are inherently fragile
- Parsers are tested against fixtures captured at a point in time, never against live sites in CI
- Solo developer may not check all 3 parsers daily -- failures go unnoticed for hours or days
- Bon Appetit embeds menu data as JavaScript objects (`Bamco.menu_items`), not semantic HTML -- regex parsing of JS is extremely brittle

**How to avoid:**
1. **Structural validation on every parse**: after scraping, validate the result against a schema (minimum X stations, minimum Y items per station, required fields present). If validation fails, return cached data and fire an alert.
2. **Parser health dashboard**: track `last_successful_parse_at` per hall per parser. Admin panel shows red/yellow/green status. Email alert if any parser fails 3+ times consecutively (circuit breaker).
3. **Fallback CSS selector chains**: for each data point, maintain 2-3 selector alternatives (e.g., primary `h1.product-title`, fallback `.main-content h1`, fallback `[data-testid="product-name"]`).
4. **Fixture versioning**: store HTML fixtures with dates. When a parser breaks in prod, capture the new HTML, update fixtures, and fix the parser. Keep old fixtures to test backwards compatibility.
5. **Scheduled canary scrape**: run all 3 parsers against live sites once per hour (not on user request). Log results. Detect breakage before users hit it.

**Warning signs:**
- Parser returns 0 menu items but no error
- Sudden drop in average items-per-station count
- One hall consistently shows no menu while others work
- Admin "last successful fetch" timestamp is >2 hours old

**Phase to address:**
Phase 1 (Core Backend) -- parsers are the foundation. Build validation and monitoring from day one, not as an afterthought.

---

### Pitfall 3: Bon Appetit JavaScript-Embedded Data Extraction

**What goes wrong:**
Bon Appetit (BAMCO) serves Collins, Malott, and McConnell -- 3 of 7 halls. Their website embeds menu data in JavaScript objects (`Bamco.menu_items`, `Bamco.dayparts`) rather than in semantic HTML. This means the parser must either: (a) use regex to extract JSON from inline script tags, or (b) use a headless browser (Puppeteer/Playwright) to execute JavaScript. Option (a) is extremely fragile. Option (b) is resource-heavy and slow, making it a poor fit for an on-demand cache-miss scrape.

**Why it happens:**
Modern food service management platforms (BAMCO, Sodexo) increasingly use single-page app (SPA) patterns. Menu data is loaded via JavaScript, not rendered in the initial HTML. Developers discover this only after their BeautifulSoup parser returns empty results.

**How to avoid:**
1. **Before building**: inspect each vendor site with browser DevTools Network tab. Check if menu data is loaded via XHR/Fetch requests that return JSON. If so, hit those endpoints directly instead of scraping HTML. Bon Appetit may expose a JSON API at paths like `cafebonappetit.com/api/2/menus?cafe={id}&date={date}` -- test this first.
2. If no JSON API exists, use **regex on inline JS** but with aggressive validation: parse the extracted JSON, validate schema, and have clear error messages when the regex fails to match.
3. **Do not default to headless browsers** for a 30-minute-TTL cache-miss path. If a headless browser is truly needed, pre-fetch on a schedule (every 15 minutes) and never run it synchronously in an API handler.
4. Test on all 3 BAMCO halls (Collins, Malott, McConnell) -- they may share a template or have slight variations.

**Warning signs:**
- BeautifulSoup returns empty results for Bon Appetit pages
- Parser works in development but fails in production (different JS rendering)
- Scrape times >5 seconds for a single page

**Phase to address:**
Phase 1 (Core Backend) -- this is a blocker. If the Bon Appetit parser approach is wrong, 3 of 7 halls have no menus.

---

### Pitfall 4: Cache Stampede on TTL Expiry During Peak Meal Times

**What goes wrong:**
At 12:00pm, hundreds of students open the app to check lunch menus. If the cache expired at 11:58am and the first scrape is still running, every subsequent request triggers another scrape. Three parsers, potentially 7 halls, all scraping simultaneously. The vendor site rate-limits or blocks the server IP. Redis gets hammered with duplicate writes. The backend CPU spikes. Users see timeouts.

**Why it happens:**
The PRD uses a flat 30-minute TTL with on-demand refresh. No locking, no request coalescing, no stale-while-revalidate. This is the textbook [cache stampede / thundering herd problem](https://www.slaknoah.com/blog/what-is-a-cache-stampede-how-to-prevent-it-using-redis).

**How to avoid:**
1. **Mutex lock per cache key**: when a cache miss occurs, acquire a Redis lock (`SETNX`) for that key. Only the lock holder runs the scrape. Other requests wait on the lock or return stale data.
2. **Probabilistic early expiration (XFetch)**: each cache read has a small probability of triggering a background refresh before actual expiry. This spreads refreshes over time.
3. **TTL jitter**: add random variance (25-35 min instead of exactly 30 min) to prevent synchronized expiry.
4. **Background refresh at 80% TTL**: at 24 minutes, proactively trigger a background scrape. The cache is always warm when users arrive.
5. **Stale-while-revalidate**: return the existing (possibly slightly stale) data immediately while refreshing in the background.

**Warning signs:**
- Vendor site returning 429 (Too Many Requests) or temporary bans
- Log entries showing 5+ concurrent scrapes for the same hall
- API latency spikes at exactly TTL intervals
- Redis `SET` operations spiking in bursts

**Phase to address:**
Phase 1 (Core Backend) -- must be solved before any significant user load hits the system.

---

### Pitfall 5: GPS Indoor Accuracy Destroys Crowding Feature Credibility

**What goes wrong:**
GPS accuracy indoors is 10-50+ meters. Dining halls are physical buildings with walls, ceilings, and neighboring structures. Students inside Frary show up as "outside the geofence" or misattributed to Frank (which is ~50m away per PRD coordinates). The crowding feature shows "Not Busy" for a packed hall because GPS scatter puts users outside the 50m radius. Students learn the feature is unreliable and ignore it.

**Why it happens:**
- Phone GPS accuracy degrades indoors to 20-50m error radius
- 50m geofence radius is barely larger than GPS error margin
- Frank and Frary are ~50m apart -- their geofences overlap
- Building materials (concrete, steel) attenuate GPS signals
- Claremont campus has dense building clusters that create multipath errors
- No alternative positioning (WiFi, BLE beacons) is available

**How to avoid:**
1. **Increase geofence radius to 75-100m** -- accept some boundary fuzziness for much better capture rate. For overlapping halls (Frank/Frary), use a combined "Pomona South" zone and split based on which building entrance is closer.
2. **Filter on GPS accuracy**: the mobile OS reports an accuracy estimate with each location fix. Discard pings with accuracy >50m. Show users "Improving location accuracy..." instead of contributing bad data.
3. **Require minimum dwell time**: only count a session in a geofence after 2+ pings (60+ seconds) within the zone. This filters out walk-throughs and GPS jitter.
4. **Ship crowding as "beta"**: label it clearly, set expectations, and collect real data before marketing it as reliable.
5. **Plan for self-reported fallback**: if GPS proves insufficient (<40% accuracy), pivot to "How busy is it?" user reports. Build the UI affordance early.

**Warning signs:**
- Crowding counts consistently lower than visually observed occupancy
- Users at Frank appearing in Frary's count (and vice versa)
- High variance in crowding levels minute-to-minute (GPS jitter)
- Location accuracy reports >30m for majority of pings

**Phase to address:**
Phase 4 (Crowding Feature) -- but the **fallback UI** should be designed in Phase 1 so the hall detail page can accommodate either GPS-based or self-reported crowding.

---

### Pitfall 6: Cold Start / Chicken-and-Egg Problem for Crowding Data

**What goes wrong:**
Crowding requires users sharing location. Users only share location if crowding data is useful. On launch day, 0 users are sharing location, so crowding shows "Estimated" for every hall. Students see no value in the crowding feature and never enable location sharing. The feature never reaches critical mass (~50 concurrent campus-wide users per PRD).

**Why it happens:**
- Network effects require a minimum viable network before providing value
- Students have trained skepticism toward location permissions
- Battery drain concerns (location services use 8-14% battery per hour per research)
- The PRD's "you must contribute to see crowding" rule actually makes cold start worse -- new users can't even see estimated data without opting in

**How to avoid:**
1. **Ship schedule-based estimates from day one**: show "Typically Busy" / "Typically Moderate" labels with clear "Based on historical patterns" disclaimer. Users see value immediately.
2. **Relax the "contribute to see" rule initially**: let all users see crowding data (estimated or real). Add "Help improve accuracy by sharing your location" prompt after they've used the feature 3+ times.
3. **Launch at Welcome Week / New Student Orientation**: highest density of students, strongest adoption window (per [campus app adoption research](https://www.raftr.com/student-engagement-strategies-to-boost-app-adoption/)).
4. **Gamify early adoption**: "You're one of 47 students helping right now" messaging. Show contribution count prominently.
5. **Target a single dining hall first**: pick the busiest (e.g., Collins or Hoch) and concentrate launch marketing. Easier to reach critical mass in one location than all 7.

**Warning signs:**
- <10 concurrent location-sharing sessions after first week
- Location permission opt-in rate <20%
- Students vocally dismissing crowding feature as useless
- High initial install rate but rapid decline in daily opens

**Phase to address:**
Phase 4 (Crowding Feature) and Phase 5 (Launch Strategy) -- but the schedule-based fallback should be built and polished in Phase 4 so it provides value on day one.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoded CSS selectors without fallbacks | Faster parser development | One vendor redesign = multi-day outage | Never -- always use fallback chains |
| Flat 30-min TTL without jitter or coalescing | Simple cache logic | Cache stampede under load | Only during local development |
| Storing menus only in Redis (not Postgres) | Fewer writes | Redis restart = total data loss, no historical data | Never -- always dual-write |
| Hardcoded geofence coordinates | No database lookup needed | Can't adjust without code deploy | Only in prototype; move to DB for Phase 4 |
| Synchronous parser in API handler | Simpler code path | User-facing latency = scrape duration | Only if stale-while-revalidate is implemented as fallback |
| Single admin email hardcoded in code | Fast to implement | Code deploy needed to change admin | Acceptable for solo dev; move to env var |
| No parser output validation | Parser is simpler | Silent data corruption (empty menus, missing stations) | Never -- always validate |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Sodexo website | Assuming static HTML; Sodexo periodically uses dynamic rendering | Check Network tab for XHR requests first; verify whether content is server-rendered or client-loaded |
| Bon Appetit (BAMCO) | Using BeautifulSoup on JavaScript-rendered pages; getting empty results | Extract `Bamco.menu_items` and `Bamco.dayparts` from inline JS, or find undocumented JSON API endpoints |
| Pomona dining | Assuming same structure as Bon Appetit; Pomona runs its own system | Build and test the Pomona parser independently; it has different HTML structure and update cadence |
| Redis (Railway) | Using default `maxmemory-policy noeviction`; Redis fills up and starts rejecting writes | Set `maxmemory-policy allkeys-lru` and monitor memory usage |
| Railway PostgreSQL | Not setting up connection pooling; hitting connection limits under load | Use connection pooling (e.g., pgBouncer or SQLAlchemy pool) from the start; Railway free tier has connection limits |
| Resend (magic link email) | Not handling email delivery delays; tokens expire before user clicks | Set token TTL to 15+ minutes; show "check spam folder" in UI; implement retry |
| Vercel + Railway CORS | Hardcoding localhost origin in CORS config; forgetting to add production domain | Use environment variable for allowed origins; add both Vercel preview and production domains |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Running all 3 parsers sequentially on first load | 15-30 second initial page load | Run parsers concurrently with `asyncio.gather()` or pre-warm cache on deploy | First user after deploy/cache flush |
| No database indexes on menus(hall_id, date, meal) | Slow menu queries as table grows | Add composite index at schema creation time | After ~1000 menu records (~6 weeks of daily menus) |
| Scanning all Redis location keys for geofence aggregation | Aggregation job takes seconds instead of milliseconds | Use Redis geospatial indexes (`GEOADD` / `GEORADIUS`) | At 200+ concurrent location sessions |
| Loading all 7 halls' menus on frontend initial render | Large payload, slow first contentful paint | Load only "What's Open Now" initially; lazy-load other halls on scroll | Any mobile user on slow connection |
| Storing full JSONB menus without compression | Redis memory fills quickly | Compress large JSON payloads before Redis storage; or store only today + tomorrow | After 2+ weeks of cached menus |
| Not paginating date range queries | Week-view loads 7 days x 7 halls x 3 meals = 147 menu records | Fetch only the selected day; prefetch adjacent days in background | Any user on the week view |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Accepting location pings from any coordinate worldwide | Attacker sends fake coordinates to inflate/deflate crowding | Validate coordinates against Claremont bounding box (lat: 34.09-34.11, lng: -117.72 to -117.70) |
| No rate limit on location endpoint per IP (only per session_id) | Attacker creates thousands of session_ids from one IP to spam fake crowding | Add per-IP rate limit (100 req/min) in addition to per-session limit (2 req/min) |
| Magic link tokens in URL without expiry | Leaked URLs grant permanent admin access | Set 10-minute token expiry; single-use tokens; invalidate on use |
| Admin endpoints accessible without CSRF protection | Cross-site request forgery could modify dining hours | Use SameSite cookies + CSRF tokens for admin session |
| No input sanitization on admin hours editor | XSS via hall names or override reason fields | Sanitize all admin inputs; use parameterized queries (SQLModel handles this, but validate JSONB inputs) |
| Vendor scraper user-agent reveals app identity | Vendor could block your specific scraper | Use a generic browser user-agent string; rotate if blocked |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing "No menu available" when parser fails | Students think the dining hall is closed | Show last cached menu with "Last updated 2 hours ago" banner; never show empty state for a hall that has hours today |
| Meal tabs showing empty tab for a meal that hasn't happened yet | Confusion: "Is there no dinner today?" | If menu not yet available for a future meal, show "Menu typically posted by [time]" |
| Date navigation defaults to today but user opened app at 11:58pm | Shows tomorrow's (mostly empty) menus because server time rolled over | Use Pacific Time explicitly for date boundaries; "today" means "the current dining day" which ends when the last meal closes (e.g., 2am for late night) |
| School color card backgrounds make text unreadable in dark mode | Accessibility failure; students can't read menu items | Test all 5 school colors against white and black text at WCAG AA contrast ratio (4.5:1); use semi-transparent overlays in dark mode |
| "What's Open Now" shows nothing at 10am because breakfast ended at 9:30am and lunch starts at 11am | Dead zone between meals makes the feature look broken | Show "Opening at 11:00am" for halls in the gap; or show "Next meal: Lunch at 11am" |
| Overwhelming list of 7 dining halls with no hierarchy | New students don't know which halls are relevant to them | Group by college; let user set preferred college to sort first; show their college's halls expanded by default |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Parsers "work":** Often missing validation that output has correct structure -- verify each parser returns >0 stations and >0 items per station, with no None/empty fields
- [ ] **Caching "works":** Often missing stampede protection -- verify that concurrent cache misses result in exactly 1 scrape, not N scrapes
- [ ] **Menu display "works":** Often missing edge cases: menus not yet posted for future dates, late-night meal crossing midnight, Oldenborg lunch-only schedule, holiday closures
- [ ] **Dark mode "works":** Often missing contrast checks on school-colored cards -- verify all 5 school colors meet WCAG AA contrast in both light and dark themes
- [ ] **"What's Open Now" works:** Often missing timezone handling -- verify it uses Pacific Time, not UTC or server local time, and handles the between-meals dead zone
- [ ] **Admin hours editor "works":** Often missing override conflict detection -- verify you can't create overlapping overrides for the same hall and meal
- [ ] **Mobile responsiveness "works":** Often missing testing on actual 375px-wide screens (iPhone SE) -- verify no horizontal scrolling on meal station grids
- [ ] **Redis caching "works":** Often missing persistence -- verify menus survive a Redis restart by also persisting to PostgreSQL
- [ ] **Rate limiting "works":** Often missing distributed correctness -- verify rate limits work across multiple backend instances (use Redis-backed rate limiter, not in-memory)

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Parser breaks due to vendor site change | MEDIUM (hours) | 1. Capture new HTML to fixtures 2. Identify changed selectors 3. Update parser + fallback selectors 4. Deploy. Cached data serves users during fix window |
| Cache stampede overwhelms vendor site | LOW (minutes) | 1. Temporarily increase Redis TTL to 6 hours 2. Manually warm cache for all halls 3. Deploy stampede fix (mutex + stale-while-revalidate) |
| GPS crowding data is wildly inaccurate | LOW (config change) | 1. Increase geofence radius 2. Tighten accuracy filter 3. Fall back to schedule-based estimates while calibrating |
| Vendor blocks server IP | MEDIUM (hours) | 1. Switch to different IP (redeploy on different Railway region) 2. Add request delays between scrapes 3. Rotate user-agent 4. Consider proxy if persistent |
| Redis runs out of memory | LOW (minutes) | 1. Flush old cache keys 2. Set maxmemory-policy to allkeys-lru 3. Increase instance size 4. Reduce TTLs |
| Admin accidentally sets wrong hours | LOW (minutes) | 1. Fix hours in admin panel 2. Changes take effect immediately (no deploy needed). Consider adding "undo last change" to admin panel |
| Cold start: no crowding data after launch | MEDIUM (weeks) | 1. Rely on schedule-based estimates 2. Ramp up campus marketing 3. Consider self-reported crowding as supplement |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Synchronous scraping on cache miss | Phase 1 (Backend) | Load test: simulate 50 concurrent menu requests; verify single scrape per hall |
| Parser brittleness | Phase 1 (Backend) | Each parser has fallback selectors, schema validation, and fixture tests. Admin dashboard shows parser health |
| Bon Appetit JS extraction | Phase 1 (Backend) | Bon Appetit parser successfully returns menus for Collins, Malott, McConnell against live site |
| Cache stampede | Phase 1 (Backend) | Under concurrent load, Redis shows exactly 1 SET per cache key per refresh cycle |
| GPS indoor accuracy | Phase 4 (Crowding) | Field test: walk through each dining hall, verify >60% of pings land within geofence |
| Cold start / adoption | Phase 5 (Launch) | Schedule-based estimates display correctly for all halls without any location data |
| Date/timezone edge cases | Phase 1 (Frontend) | Test at 11:58pm, 12:01am, between-meals gap, late-night crossing midnight, all in Pacific Time |
| Dark mode contrast | Phase 1 (Frontend) | All 5 school color cards pass WCAG AA contrast check in both light and dark mode |
| Admin hours conflicts | Phase 1 (Admin Panel) | Attempt to create overlapping overrides; system rejects or warns |
| Rate limiting across instances | Phase 1 (Backend) | Hit location endpoint from same IP 200 times in 1 minute; verify 429 after limit |

## Sources

- [RPI Sodexo Menu Scraper (broken by site change)](https://github.com/JelloRanger/menu-scraper) -- real-world example of parser brittleness
- [Reed College Bon Appetit Menu App](https://github.com/Merlin04/reed-commons-menu) -- Bon Appetit legacy API shutdown
- [Carleton Bon Appetit API Scraper](https://github.com/Machyne/pal/blob/master/api/bonapp/bon_api.py) -- regex-based Bamco.menu_items extraction
- [5CMenu (Claremont, original)](https://github.com/annechristy/5CMenu) -- prior art, 5C-specific dining app
- [5cmenu by ccorcos](https://github.com/ccorcos/5cmenu) -- prior art, 5C dining hall menus
- [Reverse Engineering Sodexo's API](https://medium.com/@andre.miras/reverse-engineering-sodexos-api-d13710b7bf0d) -- Sodexo API discovery approach
- [What is a Cache Stampede? How to Prevent It Using Redis](https://www.slaknoah.com/blog/what-is-a-cache-stampede-how-to-prevent-it-using-redis) -- stampede prevention patterns
- [How to Handle Cache Stampede in Redis (OneUptime, 2026)](https://oneuptime.com/blog/post/2026-01-21-redis-cache-stampede/view) -- TTL jitter, mutex, XFetch patterns
- [How to Build Cache Stampede Prevention (OneUptime, 2026)](https://oneuptime.com/blog/post/2026-01-30-cache-stampede-prevention/view) -- single-flight pattern
- [CSS Selector Fallback Strategies (WebScraping.AI)](https://webscraping.ai/faq/css-selectors/how-do-i-handle-if-a-website-changes-and-my-css-selectors-no-longer-work) -- fallback selector chains
- [Web Scraper Monitoring (ScrapeOps)](https://scrapeops.io/monitoring-scheduling/) -- parser health monitoring patterns
- [Fix Inaccurate Web Scraping Data (BrightData, 2026)](https://brightdata.com/blog/web-data/fix-inaccurate-web-scraping-data) -- structural change detection
- [Campus App Adoption Strategies (raftr, 2025)](https://www.raftr.com/campus-app-adoption-strategies-for-2025/) -- college app cold start
- [Geofencing Attendance Systems](https://attendanceradar.com/geofencing-attendance-systems-what-you-should-know/) -- GPS spoofing, battery drain, indoor accuracy
- [SQLModel Async FastAPI Gotchas](https://github.com/fastapi/sqlmodel/discussions/1110) -- async session issues
- [FastAPI SQLModel Async Setup (TestDriven.io)](https://testdriven.io/blog/fastapi-sqlmodel/) -- async driver requirements
- [Stop Getting Blocked: 10 Common Web-Scraping Mistakes](https://www.firecrawl.dev/blog/web-scraping-mistakes-and-fixes) -- IP rotation, headless browser overhead
- [Critical Caching Patterns (Medium, 2025)](https://medium.com/@rachoork/critical-caching-patterns-preventing-catastrophic-failures-at-scale-ddc75ac0e863) -- stale-while-revalidate, atomic swap

---
*Pitfalls research for: 5C Dining Hall Menu App (v2 rewrite)*
*Researched: 2026-02-07*
