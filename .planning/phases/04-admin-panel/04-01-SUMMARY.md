---
phase: 04-admin-panel
plan: 01
subsystem: auth
tags: [jwt, pyjwt, resend, magic-link, fastapi, cors, admin]

# Dependency graph
requires:
  - phase: 02-api-caching
    provides: "FastAPI app, config, routers, dependencies pattern"
provides:
  - "Magic link auth service (create/verify tokens, send email, require_admin dependency)"
  - "Admin API router at /api/v2/admin with auth endpoints"
  - "ParserRun SQLModel table for health tracking"
  - "Admin request/response Pydantic schemas"
  - "CORS updated for POST/PUT/DELETE/OPTIONS methods"
affects: [04-02, 04-03, 04-04]

# Tech tracking
tech-stack:
  added: [pyjwt, resend]
  patterns: [magic-link-auth, anti-enumeration-response, cookie-session]

key-files:
  created:
    - backend/app/services/auth_service.py
    - backend/app/routers/admin.py
    - backend/app/schemas/admin.py
    - backend/app/models/parser_run.py
  modified:
    - backend/app/config.py
    - backend/app/main.py
    - backend/requirements.txt

key-decisions:
  - "PyJWT over python-jose for JWT handling (lighter, actively maintained)"
  - "Magic link auth with anti-enumeration (always 200 on request-link)"
  - "7-day session tokens in httpOnly secure cookies"
  - "ParserRun model with status enum as string field (not Python enum)"

patterns-established:
  - "Auth service pattern: pure functions for token ops, FastAPI dependency for auth gate"
  - "Anti-enumeration: auth endpoints always return 200 regardless of email match"
  - "Admin schemas use Pydantic BaseModel with str for time/date fields (ISO format)"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 4 Plan 1: Admin Auth Foundation Summary

**Magic link auth via PyJWT + Resend with anti-enumeration, admin router, ParserRun model, and CORS expansion**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T10:27:55Z
- **Completed:** 2026-02-09T10:30:08Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Magic link authentication flow: request-link (anti-enumeration) and verify (sets httpOnly session cookie)
- Auth service with create/verify tokens, session management, and require_admin FastAPI dependency
- ParserRun SQLModel table ready for parser health tracking
- Full set of admin schemas (auth, hours CRUD, overrides CRUD, parser health)
- CORS middleware expanded from GET-only to all HTTP methods

## Task Commits

Each task was committed atomically:

1. **Task 1: Config, ParserRun model, and admin schemas** - `4dd5753` (feat)
2. **Task 2: Auth service, admin router, and CORS update** - `069a430` (feat)

## Files Created/Modified
- `backend/app/services/auth_service.py` - Magic link JWT creation/verification, session tokens, require_admin dependency
- `backend/app/routers/admin.py` - Admin API router with request-link, verify, logout endpoints
- `backend/app/schemas/admin.py` - Pydantic schemas for auth, hours, overrides, parser health
- `backend/app/models/parser_run.py` - ParserRun SQLModel table for health monitoring
- `backend/app/config.py` - Added admin_email, resend_api_key, jwt_secret, frontend_url, admin_from_email
- `backend/app/main.py` - Admin router registration, CORS method expansion
- `backend/requirements.txt` - Added pyjwt and resend dependencies

## Decisions Made
- PyJWT for JWT handling (lighter than python-jose, actively maintained, plan specified it)
- Magic link tokens expire in 15 minutes, session tokens in 7 days
- Anti-enumeration pattern: POST /auth/request-link always returns 200 with same message
- Session stored in httpOnly secure cookie with samesite=lax
- ParserRun status as string field rather than Python enum (flexible for future status values)
- Admin schemas use str for all time/date fields (ISO format strings, backend converts internally)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing pyjwt and resend packages**
- **Found during:** Task 2 (Auth service verification)
- **Issue:** `import resend` failed because package was added to requirements.txt but not installed in local environment
- **Fix:** Ran `pip install pyjwt>=2.11.0 resend>=2.21.0`
- **Files modified:** None (runtime environment only)
- **Verification:** All imports succeed, auth token round-trip passes
- **Committed in:** N/A (pip install, not a code change)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial -- local pip install to match requirements.txt. No scope creep.

## Issues Encountered
None beyond the dependency installation above.

## User Setup Required

This plan defines environment variables needed for production magic link auth. Before deploying:

| Variable | Source |
|----------|--------|
| `FIVEC_RESEND_API_KEY` | Resend Dashboard (https://resend.com) -> API Keys |
| `FIVEC_ADMIN_EMAIL` | The email address of the single admin user |
| `FIVEC_JWT_SECRET` | Generate with: `python -c 'import secrets; print(secrets.token_hex(32))'` |
| `FIVEC_FRONTEND_URL` | Frontend URL (e.g., https://menu.5c.edu) |

Default values allow local development without these being set.

## Next Phase Readiness
- Auth service and require_admin dependency ready for use by plans 04-02 (hours CRUD), 04-03 (overrides), 04-04 (parser health)
- ParserRun model ready for health tracking endpoints
- Admin schemas ready for CRUD endpoint implementation
- All 90 existing tests still pass -- no regressions

## Self-Check: PASSED

- All 7 claimed files exist on disk
- Commit `4dd5753` (Task 1) found in git log
- Commit `069a430` (Task 2) found in git log

---
*Phase: 04-admin-panel*
*Completed: 2026-02-09*
