# Phase 4: Admin Panel - Research

**Researched:** 2026-02-09
**Domain:** Authentication (magic link), CRUD admin UI, parser health monitoring
**Confidence:** MEDIUM-HIGH

## Summary

Phase 4 adds an admin panel to the existing 5C Menu app so a single administrator can manage dining hours, create holiday overrides, and monitor parser health. The phase spans four requirements: magic link authentication (ADM-01), hours grid editing (ADM-02), date overrides (ADM-03), and a parser health dashboard (ADM-04).

The backend work requires: (1) a magic link auth flow using Resend for email delivery and PyJWT for token signing, with a session cookie returned on verification; (2) CRUD endpoints for DiningHours and DiningHoursOverride models (both already exist in the database); (3) a new ParserRun model to track parser execution history for the health dashboard. The frontend work requires: (1) an `/admin` route group in the existing Next.js app with its own layout; (2) a login page that requests a magic link; (3) an hours grid editor (halls x days); (4) an overrides manager; (5) a parser health dashboard.

**Primary recommendation:** Use PyJWT for token signing (FastAPI-recommended), Resend Python SDK for email delivery, HttpOnly session cookies for auth state, and Next.js App Router `/admin` nested layout with middleware for route protection. Keep the admin UI simple -- no rich component libraries needed; Tailwind utility classes suffice for forms, tables, and status indicators.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.11.0 | JWT token creation/verification for magic links and session tokens | FastAPI docs now recommend PyJWT over deprecated python-jose |
| resend | 2.21.0 | Send magic link emails | Specified in ADM-01; simple Python SDK, no SMTP setup needed |
| jose (npm) | already in Next.js | Client-side JWT handling for session cookies | Next.js official auth docs use jose for encrypt/decrypt |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| itsdangerous | 2.2.0 | Alternative URL-safe timed token signing | Could replace PyJWT for magic link tokens specifically (simpler API for one-time tokens), but PyJWT is already needed for session JWTs so prefer one library |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | itsdangerous URLSafeTimedSerializer | Simpler for magic link tokens, but then need PyJWT anyway for session JWTs. One library is simpler. |
| Resend | SMTP (smtplib) | Free, but requires SMTP server config, deliverability issues, more code |
| Custom auth | NextAuth.js / Auth.js | Heavier, designed for multi-provider OAuth; overkill for single-admin magic link |
| HttpOnly cookies | Bearer tokens in localStorage | Cookies are more secure (no XSS exposure), align with Next.js official auth guidance |

**Installation:**
```bash
# Backend
pip install pyjwt resend

# Frontend (no new packages needed -- jose already available via Next.js)
```

## Architecture Patterns

### Recommended Project Structure

Backend additions:
```
backend/app/
├── models/
│   └── parser_run.py       # NEW: ParserRun model for health tracking
├── routers/
│   └── admin.py            # NEW: Admin API endpoints (auth + CRUD)
├── schemas/
│   └── admin.py            # NEW: Request/response schemas for admin endpoints
├── services/
│   ├── auth_service.py     # NEW: Magic link + session token logic
│   └── hours_service.py    # EXISTING: Add CRUD operations
└── config.py               # ADD: admin_email, resend_api_key, jwt_secret settings
```

Frontend additions:
```
web/src/app/
├── admin/
│   ├── layout.tsx          # Admin layout (sidebar? minimal header)
│   ├── page.tsx            # Redirect to /admin/hours or dashboard
│   ├── login/
│   │   └── page.tsx        # Magic link request form
│   ├── verify/
│   │   └── page.tsx        # Magic link verification handler
│   ├── hours/
│   │   └── page.tsx        # Hours grid editor (ADM-02)
│   ├── overrides/
│   │   └── page.tsx        # Date overrides manager (ADM-03)
│   └── health/
│       └── page.tsx        # Parser health dashboard (ADM-04)
├── ...existing routes...
web/src/
├── lib/
│   ├── admin-api.ts        # NEW: Admin API client with auth headers
│   └── session.ts          # NEW: Cookie-based session management
├── middleware.ts            # NEW: Protect /admin/* routes
```

### Pattern 1: Magic Link Authentication Flow

**What:** Passwordless login via email-delivered one-time token
**When to use:** ADM-01, single admin user, no password management needed

**Flow:**
```
1. Admin enters email at /admin/login
2. POST /api/v2/admin/auth/request-link { email }
3. Backend validates email matches FIVEC_ADMIN_EMAIL env var
4. Backend creates JWT with { sub: email, exp: +15min, purpose: "magic_link" }
5. Backend sends email via Resend with link: {FRONTEND_URL}/admin/verify?token={jwt}
6. Admin clicks link in email
7. Frontend /admin/verify page sends POST /api/v2/admin/auth/verify { token }
8. Backend verifies JWT, checks purpose claim, checks expiry
9. Backend returns session JWT (longer-lived, e.g., 7 days)
10. Frontend sets session JWT in HttpOnly cookie
11. Subsequent admin requests include cookie automatically
```

**Backend example:**
```python
# Source: FastAPI official docs (https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = settings.jwt_secret  # from env: FIVEC_JWT_SECRET
ALGORITHM = "HS256"
MAGIC_LINK_EXPIRE_MINUTES = 15
SESSION_EXPIRE_DAYS = 7

def create_magic_link_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire, "purpose": "magic_link"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_magic_link_token(token: str) -> str:
    """Returns email if valid, raises on expiry/tamper."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("purpose") != "magic_link":
        raise ValueError("Invalid token purpose")
    return payload["sub"]

def create_session_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS)
    payload = {"sub": email, "exp": expire, "purpose": "session"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### Pattern 2: Admin Route Protection (FastAPI Dependency)

**What:** FastAPI dependency that validates session cookie/token for admin endpoints
**When to use:** All admin CRUD endpoints

```python
# Source: FastAPI docs dependency injection pattern
from fastapi import Depends, HTTPException, Cookie

async def require_admin(session_token: str | None = Cookie(default=None, alias="admin_session")):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "session":
            raise HTTPException(status_code=401, detail="Invalid session")
        return payload["sub"]  # returns admin email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Usage in router:
@router.get("/hours")
async def list_hours(
    admin_email: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    ...
```

### Pattern 3: Next.js Middleware for Admin Route Protection

**What:** Optimistic route protection at the edge, redirecting unauthenticated users
**When to use:** All `/admin/*` routes except `/admin/login` and `/admin/verify`

```typescript
// Source: Next.js official docs (https://nextjs.org/docs/app/guides/authentication)
// web/src/middleware.ts
import { NextRequest, NextResponse } from 'next/server'

const publicAdminPaths = ['/admin/login', '/admin/verify']

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  if (pathname.startsWith('/admin') && !publicAdminPaths.includes(pathname)) {
    const session = req.cookies.get('admin_session')?.value
    if (!session) {
      return NextResponse.redirect(new URL('/admin/login', req.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*'],
}
```

**Important:** Middleware provides optimistic checks only. The backend `require_admin` dependency is the true security gate. Even if someone bypasses middleware, API calls will fail without a valid cookie.

### Pattern 4: Parser Health Tracking Model

**What:** Database table to record each parser execution with outcome
**When to use:** ADM-04, tracking success/failure rates and last fetch times

```python
import datetime as _dt
from sqlmodel import Field, SQLModel

class ParserRun(SQLModel, table=True):
    """Records each parser execution for health monitoring."""
    __tablename__ = "parser_runs"

    id: int | None = Field(default=None, primary_key=True)
    hall_id: str = Field(foreign_key="dining_halls.id", index=True)
    started_at: _dt.datetime = Field(default_factory=lambda: _dt.datetime.now(_dt.timezone.utc))
    duration_ms: int | None = None
    status: str = Field(max_length=20)  # "success", "error", "timeout", "validation_failed"
    error_message: str | None = Field(default=None, max_length=500)
    menu_date: _dt.date | None = None
```

The `get_menu_with_fallback` function in `app/parsers/fallback.py` is the ideal instrumentation point -- it already wraps the full parse lifecycle and catches all failure modes.

### Pattern 5: Hours CRUD API Design

**What:** REST endpoints for managing DiningHours and DiningHoursOverride
**When to use:** ADM-02, ADM-03

```
GET    /api/v2/admin/hours                    # All hours for all halls (grid view)
PUT    /api/v2/admin/hours/{id}               # Update a single hours entry
POST   /api/v2/admin/hours                    # Create a new hours entry
DELETE /api/v2/admin/hours/{id}               # Delete an hours entry

GET    /api/v2/admin/overrides                # All overrides (optionally filtered by date range)
POST   /api/v2/admin/overrides               # Create override
PUT    /api/v2/admin/overrides/{id}          # Update override
DELETE /api/v2/admin/overrides/{id}          # Delete override

GET    /api/v2/admin/health                   # Parser health summary (last fetch, error rates)
```

All admin endpoints require `Depends(require_admin)`.

### Anti-Patterns to Avoid

- **Storing passwords:** This is passwordless auth -- never store or compare passwords. The only credential is an email address checked against an env var.
- **Trusting middleware alone for security:** Next.js middleware is optimistic only (recent CVE-2025-29927 showed it can be bypassed). All real authorization must happen at the API level via `require_admin` dependency.
- **Putting admin routes in a separate root layout:** This would cause full page reloads when navigating between student and admin views. Use a nested layout under `app/admin/` instead.
- **Using localStorage for admin session:** HttpOnly cookies are immune to XSS. Never store auth tokens in localStorage or sessionStorage.
- **Over-engineering the UI:** Single admin user, simple forms. No need for a component library like shadcn/ui or MUI. Tailwind utility classes are sufficient.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email delivery | Custom SMTP integration | Resend Python SDK | Deliverability, SPF/DKIM handled, simple API |
| JWT signing/verification | Custom crypto or HMAC | PyJWT | Battle-tested, handles expiry, standard claims |
| Token URL encoding | Manual base64 encoding | PyJWT (already URL-safe) | JWT tokens are already URL-safe by spec |
| Cookie management (frontend) | Manual document.cookie parsing | Next.js `cookies()` API | Server-side, type-safe, HttpOnly support |
| CORS for admin endpoints | Separate CORS config | Existing FastAPI CORSMiddleware | Just add admin methods to allowed_methods |

**Key insight:** The admin panel is fundamentally simple CRUD with auth. The magic link flow is the most complex piece but follows a well-documented pattern. Resist the urge to add OAuth, role-based access, or multi-tenant features.

## Common Pitfalls

### Pitfall 1: Magic Link Token Replay

**What goes wrong:** Attacker intercepts magic link email and uses the token multiple times
**Why it happens:** JWT tokens are valid until expiry -- no built-in one-time-use guarantee
**How to avoid:** After successful verification, store the token's `jti` (JWT ID) claim in Redis with the same TTL as the token. Before verifying, check if `jti` already exists in Redis (already used). This adds one Redis check but prevents replay.
**Warning signs:** Multiple sessions created from the same magic link token

### Pitfall 2: CORS Missing POST/PUT/DELETE for Admin

**What goes wrong:** Admin frontend gets CORS errors when trying to create/update/delete
**Why it happens:** Existing CORSMiddleware only allows `GET` methods (line 28 of main.py: `allow_methods=["GET"]`)
**How to avoid:** Update `allow_methods` to include `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` or use `["*"]`. The `require_admin` dependency handles authorization.
**Warning signs:** 405 Method Not Allowed or CORS preflight failures from admin pages

### Pitfall 3: Cookie Not Sent Cross-Origin

**What goes wrong:** Admin session cookie set by backend is not sent on subsequent requests from frontend
**Why it happens:** Cookie `SameSite` attribute mismatch or different origins between frontend (Vercel) and backend (Railway)
**How to avoid:** Set cookie with `SameSite=None; Secure=true` for cross-origin, or proxy admin API calls through Next.js API routes (same-origin). The proxy approach is simpler and avoids third-party cookie issues entirely.
**Warning signs:** Auth works in development (same localhost) but fails in production

### Pitfall 4: Alembic Migration for New Table

**What goes wrong:** New `ParserRun` model is added but no migration is created, so the table doesn't exist in production
**Why it happens:** SQLModel.metadata.create_all only runs in dev/test; production relies on Alembic migrations
**How to avoid:** After adding the ParserRun model, run `alembic revision --autogenerate -m "add parser_runs table"` and `alembic upgrade head`
**Warning signs:** `ProgrammingError: relation "parser_runs" does not exist` in production

### Pitfall 5: Admin Email Env Var Not Set

**What goes wrong:** Anyone can request a magic link because the email validation is missing or misconfigured
**Why it happens:** Forgetting to set FIVEC_ADMIN_EMAIL or checking against a default value
**How to avoid:** Make `admin_email` a required setting in `config.py` with no default. The app will fail to start if it's not set (Pydantic validation).
**Warning signs:** Magic link emails sent to unauthorized addresses

### Pitfall 6: Hours Grid State Management Complexity

**What goes wrong:** The hours grid editor becomes a mess of local state trying to track edits across 7 halls x 7 days x 5 meals
**Why it happens:** Trying to batch-update all changes at once with optimistic UI
**How to avoid:** Keep it simple: each cell edit triggers an individual PUT request. Use TanStack Query's `useMutation` with `invalidateQueries` to refresh the grid. The admin is a single user -- no need for optimistic updates or conflict resolution.
**Warning signs:** Complex form state management, stale data issues, undo/redo logic

## Code Examples

### Sending a Magic Link Email (Backend)

```python
# Source: Resend Python SDK docs (https://resend.com/docs/send-with-python)
import resend
from app.config import get_settings

def send_magic_link_email(email: str, token: str) -> None:
    settings = get_settings()
    resend.api_key = settings.resend_api_key

    magic_link_url = f"{settings.frontend_url}/admin/verify?token={token}"

    params: resend.Emails.SendParams = {
        "from": f"5C Menu Admin <{settings.admin_from_email}>",
        "to": [email],
        "subject": "Your 5C Menu Admin Login Link",
        "html": f"""
            <h2>5C Menu Admin Login</h2>
            <p>Click the link below to log in. This link expires in 15 minutes.</p>
            <p><a href="{magic_link_url}">Log in to Admin Panel</a></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
        """,
    }

    resend.Emails.send(params)
```

### Admin Router Structure (Backend)

```python
# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.services.auth_service import (
    create_magic_link_token,
    verify_magic_link_token,
    create_session_token,
    require_admin,
    send_magic_link_email,
)
from app.schemas.admin import (
    MagicLinkRequest,
    MagicLinkVerify,
    SessionResponse,
    HoursUpdate,
    OverrideCreate,
)

router = APIRouter(tags=["admin"])

@router.post("/auth/request-link")
async def request_magic_link(body: MagicLinkRequest):
    """Send magic link to admin email. Always returns 200 to prevent email enumeration."""
    settings = get_settings()
    if body.email.lower() == settings.admin_email.lower():
        token = create_magic_link_token(body.email)
        send_magic_link_email(body.email, token)
    # Always return success to prevent email enumeration
    return {"message": "If this email is registered, a login link has been sent."}

@router.post("/auth/verify")
async def verify_magic_link(body: MagicLinkVerify):
    """Verify magic link token and return session cookie."""
    try:
        email = verify_magic_link_token(body.token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired link")
    session_token = create_session_token(email)
    response = JSONResponse(content={"message": "Authenticated"})
    response.set_cookie(
        key="admin_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response
```

### Next.js Admin Layout

```typescript
// web/src/app/admin/layout.tsx
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <nav className="border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-semibold">5C Menu Admin</h1>
          <div className="flex gap-4 text-sm">
            <a href="/admin/hours" className="hover:underline">Hours</a>
            <a href="/admin/overrides" className="hover:underline">Overrides</a>
            <a href="/admin/health" className="hover:underline">Parser Health</a>
          </div>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto p-4">
        {children}
      </main>
    </div>
  )
}
```

### Parser Health Instrumentation

```python
# In app/parsers/fallback.py, wrapping get_menu_with_fallback
import time

async def get_menu_with_fallback_instrumented(
    parser, hall_id, target_date, session
):
    """Wrapper that records parser runs for health dashboard."""
    start = time.monotonic()
    status = "success"
    error_msg = None

    try:
        menu, is_stale, fetched_at = await get_menu_with_fallback(
            parser, hall_id, target_date, session
        )
        if menu is None:
            status = "no_data"
        elif is_stale:
            status = "fallback"
        return menu, is_stale, fetched_at
    except Exception as exc:
        status = "error"
        error_msg = str(exc)[:500]
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        run = ParserRun(
            hall_id=hall_id,
            duration_ms=duration_ms,
            status=status,
            error_message=error_msg,
            menu_date=target_date,
        )
        session.add(run)
        await session.commit()
```

### Parser Health Query (Dashboard API)

```python
# Query: last successful fetch and error rate per hall
from sqlalchemy import func, case

async def get_parser_health(session: AsyncSession) -> list[dict]:
    """Return health summary per hall: last success, recent error rate."""
    # Last 24 hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    stmt = (
        select(
            ParserRun.hall_id,
            func.max(
                case(
                    (ParserRun.status == "success", ParserRun.started_at),
                    else_=None,
                )
            ).label("last_success"),
            func.count().label("total_runs"),
            func.sum(
                case((ParserRun.status != "success", 1), else_=0)
            ).label("error_count"),
        )
        .where(ParserRun.started_at >= cutoff)
        .group_by(ParserRun.hall_id)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "hall_id": row.hall_id,
            "last_success": row.last_success.isoformat() if row.last_success else None,
            "total_runs_24h": row.total_runs,
            "error_count_24h": row.error_count,
            "error_rate": round(row.error_count / row.total_runs * 100, 1) if row.total_runs > 0 else 0,
        }
        for row in rows
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT in FastAPI | PyJWT (FastAPI docs updated) | 2025 | python-jose deprecated, incompatible with Python >= 3.10 |
| passlib for password hashing | pwdlib[argon2] | 2025 | Not relevant here (passwordless), but noted for completeness |
| Next.js API routes for auth | Middleware + DAL pattern | Next.js 14+ | Middleware for optimistic checks, DAL for secure verification |
| localStorage for auth tokens | HttpOnly cookies | Long-standing best practice | XSS protection; Next.js official docs strongly recommend cookies |

**Deprecated/outdated:**
- python-jose: No longer maintained, compatibility issues. Use PyJWT.
- `datetime.utcnow()`: Deprecated in Python 3.12. Use `datetime.now(timezone.utc)`.
- Next.js middleware as sole auth gate: CVE-2025-29927 showed middleware can be bypassed. Always verify at the data access layer.

## Open Questions

1. **Cross-origin cookie strategy**
   - What we know: Frontend (Vercel) and backend (Railway) are on different origins in production. HttpOnly cookies with `SameSite=Lax` won't work cross-origin.
   - What's unclear: Whether to use Next.js API route proxying (simpler) or `SameSite=None; Secure` (requires HTTPS, may have browser restrictions).
   - Recommendation: Use Next.js API routes as a proxy for admin API calls. This keeps everything same-origin and avoids third-party cookie complexity. The proxy pattern is: `/api/admin/*` in Next.js forwards to FastAPI backend. Alternatively, set the session cookie at the frontend level after receiving the session JWT from the verify endpoint (store JWT in a Next.js-managed HttpOnly cookie using `cookies().set()`).

2. **Resend sender domain**
   - What we know: Resend requires a verified sender domain for production email delivery.
   - What's unclear: What domain the admin will use (e.g., `admin@5cmenu.com` or a Resend test domain).
   - Recommendation: Start with Resend's built-in `onboarding@resend.dev` for development. Document that a custom domain must be verified in Resend dashboard before production deployment.

3. **Parser health data retention**
   - What we know: The ParserRun table will grow indefinitely (7 halls x multiple runs per day).
   - What's unclear: How long to retain data and whether to prune old records.
   - Recommendation: Keep 30 days of data. Add a periodic cleanup (could be a simple SQL DELETE in an admin endpoint or scheduled task). At ~7 halls x ~30 runs/day x 30 days = ~6,300 rows/month -- trivial for PostgreSQL.

4. **Token replay prevention scope**
   - What we know: JWT magic link tokens can be reused until expiry without a server-side blacklist.
   - What's unclear: Whether this is an acceptable risk for a single-admin college dining app.
   - Recommendation: For v1, the 15-minute expiry window is sufficient. The threat model is low (single known admin). If desired, add Redis-based jti tracking later.

## Sources

### Primary (HIGH confidence)
- FastAPI official docs: JWT authentication pattern with PyJWT - https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- Next.js official docs: Authentication guide with middleware + DAL pattern - https://nextjs.org/docs/app/guides/authentication
- Resend Python SDK docs - https://resend.com/docs/send-with-python
- PyPI resend package v2.21.0 - https://pypi.org/project/resend/

### Secondary (MEDIUM confidence)
- PyJWT 2.11.0 usage docs - https://pyjwt.readthedocs.io/en/latest/usage.html
- itsdangerous 2.2.0 URL-safe timed serializer - https://itsdangerous.palletsprojects.com/en/stable/url_safe/
- FastAPI python-jose deprecation discussion - https://github.com/fastapi/fastapi/discussions/9587
- Next.js route groups for admin layouts - https://nextjs.org/docs/app/api-reference/file-conventions/route-groups

### Codebase Analysis (HIGH confidence)
- Existing DiningHours and DiningHoursOverride models in `backend/app/models/dining_hours.py` -- CRUD targets already defined
- Existing hours_service.py in `backend/app/services/` -- override precedence logic already implemented for read path
- No existing admin endpoints, auth, or parser health tracking in codebase
- CORS middleware currently only allows GET methods (`allow_methods=["GET"]` in main.py line 28)
- Settings use `FIVEC_` env prefix (config.py)
- Dependency injection via `app.dependencies` module

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyJWT and Resend are well-documented, FastAPI patterns are official
- Architecture: MEDIUM-HIGH - Auth flow is standard but cross-origin cookie strategy needs runtime validation
- Pitfalls: HIGH - Well-known issues with cookie SameSite, CORS methods, migration management
- Parser health model: MEDIUM - Design is straightforward but instrumentation approach needs to avoid complicating the existing fallback flow

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable domain, unlikely to change rapidly)
