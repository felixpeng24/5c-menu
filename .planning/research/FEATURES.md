# Feature Research

**Domain:** College dining hall menu app (multi-campus, Claremont Colleges consortium)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete. Every competitive 5C dining tool (menu.jojodmo.com, 5menu.io, the old 5Cs Menu iOS app) ships these. Students will not switch from an existing tool to one that lacks any of these.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Daily menus for all 7 halls | Core value proposition. Every competitor shows menus. Without this the app has no reason to exist. | HIGH | Requires 3 separate parsers (Sodexo, Bon Appetit, Pomona). Parser reliability is the #1 technical risk. Already scoped in Phase 1. |
| Meal-period organization (Breakfast / Lunch / Dinner) | Students need to know what is being served *now*, not scan a wall of text. Dine On Campus, Nutrislice, UCSC Menu, and menu.jojodmo.com all organize by meal period. | LOW | Tab UI. Data comes from parsers. Include late-night where applicable. |
| Station/category grouping within meals | Vendors organize food by station (Grill, Salad Bar, Entree, etc.). Without station grouping, a long flat list of items is overwhelming. menu.jojodmo.com and the v1 app both do this. | MEDIUM | Parsers must extract station names. Station ordering/filtering logic from v1 PHP needs to be replicated. |
| Open/closed status per hall | Students need to know "can I eat there right now?" at a glance. Every competitor shows this. Color-coded open/closed badges are standard (green = open, red = closing soon, gray = closed). | MEDIUM | Requires accurate hours data. Admin panel needed for hours management and overrides. Time-zone-aware comparison against current time. |
| Dining hall hours display | Students check hours constantly, especially for halls with irregular schedules (Oldenborg lunch-only). This is the #2 most-viewed data after the menu itself. | LOW | Static data managed through admin panel. Display alongside each hall card. |
| Date navigation (future menus) | Students plan meals ahead. The existing 5Cs Menu app, menu.jojodmo.com, UCSC Menu, and Nutrislice all support future date browsing. 7-day window is standard. | LOW | Horizontal date bar. API returns menus by date. Already scoped. |
| Mobile-responsive design | ~90%+ of college students access on phones. If it doesn't work well on a 375px-wide screen, it's unusable. menu.jojodmo.com is responsive. | LOW | Mobile-first Tailwind. Already scoped. |
| Fast load times (<2s) | Students check the menu in the 30 seconds between classes. Slow = abandoned. The old 5Cs Menu iOS app got praise specifically for being quick. Competitor web apps that lag get abandoned. | MEDIUM | Redis caching (30min TTL). Client-side rendering with React Query. Minimal JS bundle. |
| Dark mode | ~33% of users use dark mode exclusively, ~33% use it sometimes. menu.jojodmo.com ships dark theme. College students skew heavily toward dark mode. System preference follow is expected. | LOW | Tailwind `dark:` classes. Follow system default. Already scoped. |
| School-specific visual identity | The 5 colleges have strong identities. Color-coding halls by school (gold = HMC, red = CMC, teal = Scripps, blue = Pomona, orange = Pitzer) is a 5C-specific table stake. menu.jojodmo.com and the v1 app both do this. | LOW | CSS variables or Tailwind config per school. Card backgrounds with school colors. Already scoped. |
| Stale data handling with timestamps | Parsers will fail. Users must know if data is fresh or stale. "Last updated X ago" is standard practice. The v1 app review complaints about wrong hours highlight how critical data freshness transparency is. | LOW | Show last-fetched timestamp per hall. Visual indicator when data is >1hr stale. Already scoped. |

### Differentiators (Competitive Advantage)

Features that set 5C Menu v2 apart from menu.jojodmo.com, 5menu.io, and the old iOS app. Not expected, but create switching incentive and retention.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| "What's Open Now" filter | One-tap to hide closed halls. Reduces cognitive load during the most common use case: "I'm hungry right now, where can I eat?" No current 5C competitor has a dedicated filter toggle for this. Dine On Campus and The Campus Dining App highlight open status but don't offer a filter. | LOW | Client-side filter on hall list. Already scoped for Phase 1. Low effort, high impact. |
| Cross-hall food search | "Where is chicken tikka masala today?" Search a dish name, see which halls serve it and when. UCSC Menu and Purdue Mobile Menus both have this. No 5C competitor does. Students with dietary needs or food preferences would find this invaluable. | MEDIUM | Requires indexing menu items across all halls/dates. Full-text search on menu items. Client-side filtering may suffice at this data scale (~500-1000 items/day). |
| Dietary/allergen icons | Display dietary labels (vegan, vegetarian, gluten-free, contains nuts, etc.) inline on menu items. Nutrislice, Bite by Sodexo, and Dine On Campus all provide this. ~8% of college students have food allergies. Vendors provide some dietary info. | MEDIUM | Dependent on what vendors expose. Sodexo's Bite platform has rich dietary data. Bon Appetit provides allergen icons. Pomona's source needs investigation. Parser must extract dietary metadata. |
| Dietary preference filter | Let users set persistent dietary preferences (e.g., "vegan") and visually highlight or filter compatible items. Nutrislice does this with unlimited icons and cross-out/highlight. Goes beyond just showing icons to actually filtering the menu view. | MEDIUM | Requires dietary icons (above) as prerequisite. Local storage for preferences (no accounts). Filter/highlight logic on menu items. |
| PWA / Add to Home Screen | Installable web app that feels native without App Store friction. Eliminates the biggest barrier to adoption for a web-first approach. 40% higher install rate than "download native app" (Lyft PWA data). Gives the app an icon on the home screen, full-screen mode, and optional offline support. | LOW | Service worker + manifest.json. Next.js has good PWA support via next-pwa. Minimal additional code for basic installability. |
| Offline menu cache | Cache today's menus so the app works in dead zones (basements, dining halls with poor signal). Service worker + Cache API. Network-first strategy: try fresh data, fall back to cache. | LOW | Natural extension of PWA. Cache the last-fetched menu JSON. Show "offline" indicator. Small addition on top of service worker. |
| Admin panel with hours management | Table editor UI for dining hours. Handles regular hours, holiday overrides, and break schedules. No other 5C tool has admin-managed hours -- they all scrape or hardcode. This means v2 can be accurate when competitors show wrong hours (a top complaint in app store reviews). | HIGH | Full CRUD UI. Date override system. Already scoped for Phase 1. This is infrastructure that enables accurate open/closed status (a table-stakes feature). |
| Parser health dashboard | Admin-visible dashboard showing last successful fetch time per parser, error rates, and failure alerts. Enables proactive maintenance rather than discovering breakdowns from user complaints. | LOW | Backend metrics + simple admin UI. Already partially scoped. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem appealing but would hurt the product, add undue complexity for a solo developer, or conflict with the project's constraints (anonymous app, solo dev, ~5000 users).

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| User accounts / authentication | "Save my dietary preferences across devices." "Track what I've eaten." | Adds significant complexity (auth flows, password resets, data storage, privacy compliance). The app is explicitly anonymous. 5000-user campus doesn't need accounts. Friction of login kills casual usage -- students check menus dozens of times per day. | Use localStorage for preferences. No login required. Preferences stay on-device. |
| Food ratings / reviews | "Let students rate dishes." Sounds engaging. | Moderation nightmare for a solo dev. Low-quality reviews ("this sucks") with no accountability (anonymous app). Dining staff may resent the feature. Small user base means ratings are statistically meaningless -- 3 votes on a dish tells you nothing. Creates adversarial relationship with dining services who control the data you scrape. | Skip entirely. If feedback matters, link to the dining hall's official feedback form. |
| Meal plan balance checking | 5menu.io's main differentiator. Students want to see Flex/Claremont Cash balance. | Requires storing student credentials (Claremont Card login). Security liability. If credentials leak, you're responsible. The colleges could revoke access at any time. Maintenance burden of credential-based scraping. This is a separate product, not a menu app feature. | Link to the official Claremont Card portal. Don't touch student credentials. |
| Mobile ordering / pre-ordering | Grubhub campus, Fresh Ideas "Dine Without the Line." Trendy feature. | Requires integration with dining hall POS systems, payment processing, and kitchen workflow. Impossible without institutional partnership. Way beyond scope for a solo dev scraping menus. | Not applicable to this product. Dining halls at the 5Cs don't support third-party ordering. |
| Real-time occupancy / crowding | UCLA's CrowdZen, Occuspace Waitz. "How busy is the dining hall?" | Requires hardware (IoT sensors, Wi-Fi monitoring infrastructure) or institutional data access. Cannot be built by scraping. Phase 4 aspiration in the roadmap, but only feasible if the colleges provide an API or data feed. Do not promise this without a data source. | Defer to Phase 4. Only build if a viable data source exists. Do not fake it with estimates. |
| Push notifications | "Notify me when my favorite dish is served." Dining Connect and FoodU offer this. | Requires notification infrastructure, user preference storage, and server-side scheduled jobs. High ongoing cost for a solo dev. Overuse leads to notification fatigue and uninstalls. Web push notifications have low opt-in rates (~5-15%). | Skip for web. Reconsider only for native mobile app (Phase 3). Even then, be very selective -- only "your favorite is being served today" is defensible. |
| Nutrition calculator / calorie tracking | Nutrislice offers meal-level calorie totals. HealthKit integration. | Requires reliable, complete nutritional data from all vendors. Data quality is inconsistent. Liability risk if nutritional info is wrong (allergen claims especially). Integration with HealthKit requires native app. | Show whatever dietary/nutrition data vendors provide, clearly labeled as sourced from vendor. Do not calculate or aggregate. Do not make health claims. |
| Social features (friends, sharing) | "See what your friends are eating." 5C Friend app tried this. | Requires user accounts (anti-feature #1). Small campus means social features feel creepy, not useful. Students already coordinate via text/GroupMe. Building a social layer is a separate product. | Not applicable. Students coordinate meals through existing messaging apps. |
| Multi-language support | Nutrislice supports 50+ languages. | 5C student body is English-speaking for academic purposes. Translation adds maintenance burden. Menu item names don't translate well ("Frank's Special Bowl" in French?). | Ship English only. |
| Apple Watch / wearable support | UCSC Menu has watchOS support. | Requires native app development for watchOS. Tiny user base for wearable usage. High maintenance cost for marginal benefit. | Defer indefinitely. Mobile web covers the "quick check" use case. |

## Feature Dependencies

```
[Daily menus for all 7 halls]
    |
    +--requires--> [3 working parsers (Sodexo, Bon Appetit, Pomona)]
    |
    +--requires--> [Meal-period organization]
    |                  |
    |                  +--requires--> [Station/category grouping]
    |
    +--enables--> [Cross-hall food search]
    |
    +--enables--> [Dietary/allergen icons]
    |                  |
    |                  +--enables--> [Dietary preference filter]
    |
    +--enables--> [Stale data handling with timestamps]

[Admin panel with hours management]
    |
    +--enables--> [Open/closed status per hall]
    |                  |
    |                  +--enables--> ["What's Open Now" filter]
    |
    +--enables--> [Dining hall hours display]
    |
    +--enables--> [Holiday/break schedule overrides]

[PWA / Add to Home Screen]
    |
    +--enables--> [Offline menu cache]

[Parser health dashboard]
    +--requires--> [3 working parsers]
    +--enhances--> [Admin panel]
```

### Dependency Notes

- **Menus require parsers:** The entire app is useless without working parsers. Parser development is the critical path and highest-risk item.
- **Open/closed requires hours data:** The admin panel for hours management must exist before open/closed status is reliable. Without admin-managed hours, the app will show wrong times (the #1 complaint about the existing 5Cs Menu app).
- **Dietary icons require parser support:** Each parser must extract dietary metadata from its vendor source. If a vendor doesn't expose this data, those items won't have dietary tags. Bon Appetit and Sodexo expose dietary info; Pomona needs investigation.
- **Dietary filter requires dietary icons:** Can't filter by "vegan" if items aren't tagged. Build icons first, filter second.
- **Food search requires menu data:** Cross-hall search is just an index over existing menu data. Low marginal cost once menus are working.
- **PWA enables offline:** Service worker is the prerequisite for offline caching. Bundle them together.
- **"What's Open Now" is cheap once hours work:** Pure client-side filter. Almost free once open/closed status is accurate.

## MVP Definition

### Launch With (v1 / Phase 1)

Minimum viable product that gives students a reason to switch from menu.jojodmo.com.

- [x] Daily menus for all 7 halls via 3 parsers -- core value, non-negotiable
- [x] Meal-period tabs (Breakfast / Lunch / Dinner) -- basic usability
- [x] Station/category grouping within meals -- readability
- [x] Open/closed status per hall -- top user need
- [x] Dining hall hours display -- top user need
- [x] Admin panel with hours management and overrides -- enables accurate status
- [x] 7-day date navigation -- standard expectation
- [x] "What's Open Now" filter toggle -- low-cost differentiator
- [x] School color card backgrounds -- 5C identity, visual polish
- [x] Dark mode (system default follow) -- user expectation
- [x] Stale data handling with timestamps -- trust and transparency
- [x] Mobile-responsive layout -- majority of usage is mobile
- [x] Parser health dashboard (admin) -- operational awareness

### Add After Validation (v1.x / Phase 2)

Features to add once Phase 1 is stable and parsers are reliable.

- [ ] Cross-hall food search -- add when menu data is stable and students request it
- [ ] Dietary/allergen icons on menu items -- add when parser dietary extraction is verified per vendor
- [ ] Dietary preference filter (localStorage) -- add after dietary icons ship
- [ ] PWA installability (manifest + service worker) -- add when core web experience is solid
- [ ] Offline menu cache -- add alongside PWA

### Future Consideration (Phase 3+)

Features to defer until product-market fit is established.

- [ ] Native mobile app (Phase 3) -- only after web app proves adoption; consider React Native or Swift
- [ ] Real-time occupancy/crowding (Phase 4) -- only if institutional data source becomes available
- [ ] Push notifications (Phase 3, native only) -- only "your favorite is being served" is worth building

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Daily menus (all 7 halls) | HIGH | HIGH | P1 |
| Meal-period tabs | HIGH | LOW | P1 |
| Station grouping | HIGH | MEDIUM | P1 |
| Open/closed status | HIGH | MEDIUM | P1 |
| Hours display | HIGH | LOW | P1 |
| Admin hours management | HIGH | HIGH | P1 |
| Date navigation (7-day) | MEDIUM | LOW | P1 |
| "What's Open Now" filter | HIGH | LOW | P1 |
| School color backgrounds | MEDIUM | LOW | P1 |
| Dark mode | MEDIUM | LOW | P1 |
| Stale data timestamps | MEDIUM | LOW | P1 |
| Mobile-responsive | HIGH | LOW | P1 |
| Parser health dashboard | MEDIUM | LOW | P1 |
| Cross-hall food search | HIGH | MEDIUM | P2 |
| Dietary/allergen icons | HIGH | MEDIUM | P2 |
| Dietary preference filter | MEDIUM | MEDIUM | P2 |
| PWA installability | MEDIUM | LOW | P2 |
| Offline cache | LOW | LOW | P2 |
| Native mobile app | MEDIUM | HIGH | P3 |
| Real-time occupancy | MEDIUM | HIGH | P3 |
| Push notifications | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch (Phase 1)
- P2: Should have, add when parsers are stable (Phase 2)
- P3: Future consideration, defer until adoption proven (Phase 3+)

## Competitor Feature Analysis

| Feature | menu.jojodmo.com | 5Cs Menu (iOS) | 5menu.io | Dine On Campus | Nutrislice | Our Approach |
|---------|-----------------|----------------|----------|----------------|------------|--------------|
| All 7 hall menus | Yes | Yes (5 colleges) | Partial (cafes) | Per-campus | Per-campus | Yes, all 7 from day one |
| Meal period tabs | Yes | Yes | No | Yes | Yes | Yes, tabs |
| Station grouping | Yes | Unclear | No | Yes | Yes | Yes, per parser logic |
| Open/closed status | Yes (color-coded) | Yes (sometimes wrong) | No | Yes | Yes | Yes, admin-managed (more accurate) |
| Hours display | Yes | Yes (buggy per reviews) | No | Yes | Yes | Yes, admin-managed with overrides |
| Date navigation | Yes (7 days) | Yes | No | Yes | Yes (full week) | Yes, 7 days |
| Dark mode | Yes (default) | No | Toggle | Varies | No | Yes, system default follow |
| School colors | Yes | Yes | No | N/A | N/A | Yes, bold card backgrounds |
| Food search | No | No | No | No | No | Phase 2 (differentiator) |
| Dietary icons | No | No | No | Limited | Yes (full) | Phase 2 (per vendor data) |
| Dietary filter | No | No | No | No | Yes (full) | Phase 2 |
| Offline support | No | Native = yes | No | Native = yes | Native = yes | Phase 2 (PWA) |
| Meal plan balance | No | No | Yes (Claremont Card) | No | No | No (anti-feature) |
| Hours overrides | Unknown | No | No | Yes | Unknown | Yes, admin-managed |
| "What's Open Now" filter | No | No | No | No | No | Yes, Phase 1 (unique) |

### Competitive Summary

The primary local competitor is **menu.jojodmo.com**, which is active, maintained, and has strong feature parity with what we're building. Its main weakness is that it has no admin-managed hours (leading to potential inaccuracies) and no food search or dietary features. The old **5Cs Menu iOS app** (v1.1.1, last updated March 2022) has strong ratings (4.8 stars) but is stale and has review complaints about wrong hours. **5menu.io** focuses on meal plan balance checking, a different product category.

Our key advantages for Phase 1 will be:
1. **Admin-managed hours with overrides** -- more accurate than any competitor
2. **"What's Open Now" filter** -- no competitor offers this as a dedicated toggle
3. **Modern web stack** -- faster development velocity for future features

Our key advantages for Phase 2 will be:
4. **Cross-hall food search** -- no 5C competitor has this
5. **Dietary filtering** -- no 5C competitor has this

## Sources

- [Dine On Campus (iOS)](https://apps.apple.com/us/app/dine-on-campus/id1170602720) -- industry-standard college dining app
- [The Campus Dining App features](https://www.thecampusdiningapp.com/features/) -- feature set reference for commercial dining apps
- [5Cs Menu iOS app](https://apps.apple.com/us/app/5cs-menu/id1477560187) -- direct competitor, 4.8 stars, last updated 2022
- [5menu.io](https://www.5menu.io/) -- 5C competitor focused on balance checking
- [menu.jojodmo.com](https://menu.jojodmo.com/) -- primary active 5C competitor
- [Bite by Sodexo](https://bite.sodexo.com/) -- dietary/allergen filtering reference
- [Nutrislice](https://nutrislice.com/) -- industry leader in allergen/dietary menu filtering
- [UCSC Menu App](https://apps.apple.com/us/app/ucsc-menu/id1670523487) -- reference for food search, occupancy features
- [FoodService Director: Mobile apps in college dining](https://www.foodservicedirector.com/colleges-universities/mobile-apps-taking-bigger-role-in-promoting-college-dining-operations) -- industry trends
- [FoodService Director: Occupancy apps](https://www.foodservicedirector.com/colleges-universities/app-allows-students-to-see-occupancy-before-deciding-where-to-eat) -- UCLA CrowdZen case study
- [Occuspace / UCLA case study](https://www.occuspace.com/case-studies/case-study-university-facility---dining) -- real-time occupancy technology
- [Grubhub Campus Dining](https://www.grubhub.com/about/campus) -- mobile ordering reference (anti-feature context)

---
*Feature research for: 5C Dining Menu App (Claremont Colleges)*
*Researched: 2026-02-07*
