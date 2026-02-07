# Stack Research

**Domain:** College dining menu web app with web scraping, Redis caching, admin panel
**Project:** 5C Menu v2 (Claremont Colleges)
**Researched:** 2026-02-07
**Confidence:** HIGH (most decisions pre-validated by developer; versions verified via PyPI/npm/official sources)

---

## Recommended Stack

### Backend — Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.13.x | Runtime | Performance gains (5-15% over 3.12), JIT compiler, reduced memory footprint. 3.12 is fallback if any dependency breaks. Railway supports both. | HIGH |
| FastAPI | 0.128.x | Web framework | Already decided. Async-first, auto OpenAPI docs, Pydantic v2 native. Perfect for this scale. | HIGH |
| SQLModel | 0.0.32 | ORM | Already decided. Thin layer over SQLAlchemy 2.0 + Pydantic v2. Less boilerplate than raw SQLAlchemy for FastAPI apps. | HIGH |
| SQLAlchemy | 2.0.46 | Database toolkit (underlying) | Required by SQLModel. Pin to 2.0.x (not 2.1.x beta). SQLModel 0.0.32 tested against 2.0.46. | HIGH |
| Pydantic | 2.12.x | Validation/serialization | Required by FastAPI and SQLModel. v2 is mature and fast. | HIGH |
| Uvicorn | 0.40.0 | ASGI server | Standard FastAPI production server. Install with `uvicorn[standard]` for uvloop + httptools. Requires Python >=3.10. | HIGH |
| PostgreSQL | 16.x | Primary database | Already decided. Source of truth for halls, hours, menus. Railway provides managed Postgres 16. | HIGH |
| Redis | 7.x | Cache + ephemeral data | Already decided. Menu cache (30min TTL), crowding sessions (2min TTL), crowding snapshots. Railway provides managed Redis. | HIGH |

### Backend — Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| redis (redis-py) | 7.1.x | Redis client | All Redis operations (caching, crowding). Async support built-in. Requires Python >=3.10. | HIGH |
| asyncpg | 0.30.x | Async Postgres driver | Used by SQLAlchemy async engine. ~5x faster than psycopg3 for async workloads. | HIGH |
| httpx | 0.28.x | HTTP client for scrapers | All 3 parsers (Sodexo, Bon Appetit, Pomona). Async + sync, HTTP/2 support, better than requests for modern scraping. | HIGH |
| selectolax | 0.4.6 | Fast HTML parser | Primary parser for all 3 scrapers. 10x faster than BeautifulSoup. CSS selector API. C-based Lexbor engine. | MEDIUM |
| beautifulsoup4 | 4.14.x | HTML parser (fallback) | Fallback if selectolax CSS selectors can't handle a particular vendor page. More forgiving with malformed HTML. | HIGH |
| Alembic | 1.18.x | Database migrations | Schema changes over time. Works with SQLModel via `target_metadata = SQLModel.metadata`. Use `--autogenerate`. | HIGH |
| resend | 2.21.x | Email API (Python SDK) | Magic link admin auth. Send login emails to single hardcoded admin email. | HIGH |
| python-jose | 3.3.x | JWT tokens | Admin session tokens after magic link verification. Lightweight, well-maintained. | MEDIUM |
| pytest | 9.0.x | Testing framework | All backend tests. Parser unit tests with HTML fixtures, API endpoint tests. | HIGH |
| pytest-asyncio | 1.3.x | Async test support | Testing async FastAPI endpoints and async database operations. | HIGH |
| httpx (TestClient) | 0.28.x | API testing | FastAPI TestClient is built on httpx. Use for endpoint tests. | HIGH |

### Frontend — Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Next.js | 15.x (stable) | React framework | Use 15.x, not 14 or 16. 14 is outdated (no React 19). 16 has breaking changes (removed `next lint`, removed sync request APIs). 15 is the sweet spot: stable, Turbopack in beta, React 19 support. | HIGH |
| React | 19.x | UI library | Bundled with Next.js 15. Stable React Compiler support. | HIGH |
| TypeScript | 5.7.x | Type safety | Non-negotiable for any 2026 project. Next.js 15 has excellent TS support. | HIGH |
| Tailwind CSS | 4.x | Styling | Already decided. v4 is stable (released Jan 2025). CSS-first config, no tailwind.config.js needed. 5x faster builds. Requires `@tailwindcss/postcss` in postcss.config.mjs. | HIGH |
| TanStack Query | 5.90.x | Server state management | Already decided. Client-side data fetching, caching, refetching. Perfect for menu data that changes throughout the day. | HIGH |
| Node.js | 22.x LTS | Runtime | Active LTS until Apr 2027. Required by Next.js 15. Do not use 20 (maintenance only) or 24 (too new). | HIGH |

### Frontend — Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| resend (Node SDK) | 6.9.x | Email API (for admin panel) | Only if admin magic link flow is handled client-side. Otherwise, backend Python SDK handles this. Likely unnecessary if backend sends the email. | LOW |
| clsx | 2.x | Conditional classnames | Combining Tailwind classes conditionally. Lightweight alternative to classnames. | HIGH |
| tailwind-merge | 3.x | Tailwind class deduplication | Use with clsx via a `cn()` utility. Prevents conflicting Tailwind classes. | HIGH |
| date-fns | 4.x | Date manipulation | Date navigation (today, tomorrow, +7 days). Lighter than dayjs/moment. Tree-shakeable. | MEDIUM |
| lucide-react | latest | Icons | Clean, consistent icon set. Used by shadcn/ui ecosystem. | MEDIUM |

### Development Tools

| Tool | Purpose | Notes | Confidence |
|------|---------|-------|------------|
| uv | Python package manager | 10-100x faster than pip. Single binary replaces pip, pip-tools, virtualenv. Use for backend. `uv init`, `uv add`, `uv sync`. | HIGH |
| pnpm 10.x | Node package manager | Faster and more disk-efficient than npm. Security by default (no auto-running install scripts). Use for web/. | HIGH |
| Ruff 0.15.x | Python linter + formatter | Replaces flake8, black, isort in one tool. 100x faster. Written in Rust. Use for all backend Python. | HIGH |
| Biome 2.3.x | JS/TS linter + formatter | Replaces ESLint + Prettier in one tool. 10-25x faster. Use for web/ frontend code. Note: Next.js 15 still ships with ESLint support, so ESLint 9 + Prettier is the safe alternative. | MEDIUM |
| ESLint 9.x + Prettier | JS/TS linter + formatter (alternative) | If Biome feels too bleeding-edge, use ESLint 9 flat config + eslint-config-next + Prettier. More ecosystem support. | HIGH |

### Infrastructure

| Technology | Purpose | Notes | Confidence |
|------------|---------|-------|------------|
| Railway | Backend hosting | FastAPI + PostgreSQL + Redis all on Railway. Dockerfile-based deployment. Already has account. | HIGH |
| Vercel | Frontend hosting | Next.js on Vercel is zero-config. Already has account. Custom domain support. | HIGH |
| Docker | Backend containerization | Dockerfile for Railway deployment. Multi-stage build: Python 3.13-slim base. | HIGH |
| GitHub Actions | CI/CD | Run tests (pytest + vitest), lint (ruff + biome/eslint), type-check on PR. | MEDIUM |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not the Alternative |
|----------|-------------|-------------|------------------------|
| Python runtime | 3.13 | 3.12 | 3.12 is safe fallback but 3.13 is stable, faster, and all key deps support it. |
| Next.js version | 15 | 16 | 16 removes `next lint`, removes sync request APIs, requires full Turbopack migration. Too many breaking changes for a greenfield that needs fast shipping. |
| Next.js version | 15 | 14 | 14 lacks React 19 support, Turbopack improvements. Already outdated. |
| ORM | SQLModel | Raw SQLAlchemy 2.0 | SQLAlchemy is more powerful but more verbose. SQLModel's Pydantic integration saves significant boilerplate for FastAPI. |
| ORM | SQLModel | Tortoise ORM | Less mature, smaller ecosystem, no Pydantic integration. SQLModel is from the FastAPI creator. |
| HTML parser | selectolax | BeautifulSoup | BS4 is 10x slower. For 3 parsers running on cache miss, speed matters. Keep BS4 as fallback for edge cases. |
| HTML parser | selectolax | lxml | lxml is fast but heavier C dependency, harder to install. selectolax is newer and even faster. |
| HTTP client | httpx | requests | requests has no async support. httpx is a drop-in replacement with async + HTTP/2. |
| HTTP client | httpx | aiohttp | aiohttp is async-only. httpx supports both sync and async in one API. Simpler for scrapers that may not need async. |
| Redis client | redis-py | aioredis | aioredis is deprecated and merged into redis-py. Just use redis-py. |
| Postgres driver | asyncpg | psycopg3 | asyncpg is ~5x faster for async workloads. psycopg3 is better if you need sync too, but FastAPI is async-first. |
| Package manager (Python) | uv | poetry | Poetry is slower, more opinionated. uv is 10-100x faster, simpler, from the Ruff team. |
| Package manager (Node) | pnpm | npm | pnpm is faster, stricter (no phantom deps), more disk-efficient. |
| Admin auth | Magic link (Resend) | Password auth | Single admin user. Magic link = no password to forget, no password storage. Resend free tier is more than enough. |
| Admin auth | Magic link (Resend) | OAuth (Google) | Overkill for single admin. Adds OAuth provider dependency. Magic link is simpler. |
| JS/TS linter | Biome or ESLint 9 | ESLint 8 | ESLint 8 is EOL. Flat config (ESLint 9) is the future. Biome is faster but less ecosystem support. |
| Styling | Tailwind v4 | Tailwind v3 | v4 is stable, faster, simpler config. No reason to use v3 on a new project. |
| Testing (frontend) | Vitest 4.x | Jest | Vitest is faster, native ESM, better DX. Jest is legacy for new projects. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| requests (Python) | No async support, slower | httpx |
| aioredis | Deprecated, merged into redis-py | redis-py 7.x |
| SQLAlchemy 2.1.x beta | Unstable, breaking changes possible | SQLAlchemy 2.0.46 (stable) |
| Pydantic v1 | Deprecated, slower, less features | Pydantic v2.12.x |
| Next.js 14 | Outdated, no React 19 | Next.js 15.x |
| Next.js 16 | Too many breaking changes for fast shipping | Next.js 15.x |
| Tailwind v3 | v4 is stable and better in every way | Tailwind v4.x |
| ESLint 8 | EOL, legacy config format | ESLint 9 flat config or Biome |
| Jest | Slower, worse ESM support | Vitest 4.x |
| pip + virtualenv | Slow, fragmented tooling | uv |
| npm | Phantom dependencies, slower | pnpm 10.x |
| Scrapy | Massive overkill for 3 simple scrapers | httpx + selectolax |
| Selenium/Playwright | Not needed unless vendor sites are JS-rendered SPAs. All 3 vendor sites appear to be server-rendered. | httpx (no browser needed) |
| Django | Wrong framework. Django is batteries-included but heavier. FastAPI is better for API-first apps with separate frontend. | FastAPI |
| Flask | No async, no auto-docs, less modern | FastAPI |
| Moment.js | Deprecated, massive bundle size | date-fns |
| Axios | Unnecessary with TanStack Query. fetch() is fine. | Native fetch + TanStack Query |
| Redux / Zustand | Overkill. No complex client state. TanStack Query handles server state. | TanStack Query |
| Prisma | Node.js ORM, wrong ecosystem (backend is Python) | SQLModel |
| shadcn/ui | Tempting but adds complexity. For a menu display app, raw Tailwind is sufficient. Only add if admin panel needs complex form components. | Raw Tailwind CSS |

---

## Stack Patterns by Variant

**If vendor sites turn out to be JavaScript-rendered SPAs:**
- Add Playwright (`playwright` Python package) for browser-based scraping
- Only for the specific vendor that requires it, not all three
- This adds ~50MB to Docker image; avoid unless truly needed

**If admin panel needs complex form components (hours editor grid):**
- Consider adding shadcn/ui (or Radix UI primitives directly)
- Only for admin routes, not the public menu pages
- Adds react-aria or radix-ui as dependencies

**If scraper reliability becomes a problem:**
- Add APScheduler or a simple cron-based health check
- Log parser failures to a simple table, surface in admin dashboard
- Do NOT add Celery (overkill for this scale)

**If crowding feature (Phase 4) needs WebSockets:**
- FastAPI has native WebSocket support
- Use for real-time crowding updates if polling proves too slow
- Do NOT add Socket.IO (unnecessary abstraction over native WS)

---

## Version Compatibility Matrix

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| SQLModel 0.0.32 | SQLAlchemy 2.0.14-2.0.46 | Do NOT use SQLAlchemy 2.1.x beta |
| SQLModel 0.0.32 | Pydantic 2.7+ | Requires Pydantic v2, not v1 |
| FastAPI 0.128.x | Pydantic 2.x | Full v2 support, also supports pydantic.v1 shim |
| FastAPI 0.128.x | Uvicorn 0.40.x | Both require Python >=3.10 |
| Next.js 15.x | React 19.x | Bundled together |
| Next.js 15.x | Tailwind CSS 4.x | Requires `@tailwindcss/postcss` in postcss config |
| Next.js 15.x | Node.js 22.x LTS | Officially supported |
| Vitest 4.x | Node.js 22.x | Compatible |
| TanStack Query 5.x | React 19.x | Full support |
| redis-py 7.1.x | Python >=3.10 | Dropped 3.9 support |
| asyncpg 0.30.x | PostgreSQL 16.x | Full support |
| Alembic 1.18.x | SQLAlchemy 2.0.46 | Full support |
| Ruff 0.15.x | Python 3.13 | Full support |

---

## Installation Commands

### Backend (Python — using uv)

```bash
# Initialize project
cd backend/
uv init --python 3.13

# Core dependencies
uv add fastapi[standard] sqlmodel alembic asyncpg redis httpx selectolax beautifulsoup4 resend python-jose[cryptography]

# Note: fastapi[standard] includes uvicorn[standard], email-validator, httptools, etc.

# Dev dependencies
uv add --dev pytest pytest-asyncio httpx ruff
```

### Frontend (Next.js — using pnpm)

```bash
# Initialize project
cd web/
pnpm create next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Core dependencies
pnpm add @tanstack/react-query clsx tailwind-merge date-fns

# Dev dependencies
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

---

## Decision: Biome vs ESLint 9

This is the one call where both options are defensible.

**Go with ESLint 9 + Prettier if:**
- You want maximum Next.js ecosystem compatibility
- You want eslint-config-next out of the box
- You prefer the larger community / more Stack Overflow answers

**Go with Biome if:**
- You want a single tool (no Prettier config)
- You want 10-25x faster linting
- You're comfortable with a newer tool (v2.3, stable since mid-2025)

**Recommendation:** Start with ESLint 9 + Prettier (safer for a solo developer shipping fast). Migrate to Biome later if desired. The migration tool makes this easy.

---

## Decision: selectolax vs BeautifulSoup

**Recommendation:** Use selectolax as primary parser, keep beautifulsoup4 as a dependency for fallback.

**Rationale:**
- selectolax is ~10x faster (0.039s vs 0.355s on benchmarks)
- CSS selector API is similar to BS4
- If a vendor page has particularly malformed HTML that selectolax chokes on, BS4 with html.parser can handle it
- Both are lightweight dependencies; having both costs nothing

---

## Sources

- [FastAPI PyPI](https://pypi.org/project/fastapi/) -- version 0.128.2 verified (HIGH)
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) -- Python 3.9+ requirement verified (HIGH)
- [SQLModel PyPI](https://pypi.org/project/sqlmodel/) -- version 0.0.32 verified (HIGH)
- [SQLModel Release Notes](https://sqlmodel.tiangolo.com/release-notes/) -- SQLAlchemy 2.0 compatibility verified (HIGH)
- [SQLAlchemy Releases](https://github.com/sqlalchemy/sqlalchemy/releases) -- version 2.0.46 verified (HIGH)
- [Pydantic PyPI](https://pypi.org/project/pydantic/) -- version 2.12.5 verified (HIGH)
- [Uvicorn PyPI](https://pypi.org/project/uvicorn/) -- version 0.40.0, Python >=3.10 verified (HIGH)
- [Next.js Blog](https://nextjs.org/blog) -- Next.js 15 and 16 status verified (HIGH)
- [Next.js 16 Upgrade Guide](https://nextjs.org/docs/app/guides/upgrading/version-16) -- breaking changes verified (HIGH)
- [Tailwind CSS v4.0 Blog](https://tailwindcss.com/blog/tailwindcss-v4) -- v4 stable Jan 2025 verified (HIGH)
- [TanStack Query npm](https://www.npmjs.com/package/@tanstack/react-query) -- version 5.90.x verified (HIGH)
- [redis-py PyPI](https://pypi.org/project/redis/) -- version 7.1.0, Python >=3.10 verified (HIGH)
- [httpx PyPI](https://pypi.org/project/httpx/) -- version 0.28.1 verified (HIGH)
- [selectolax PyPI](https://pypi.org/project/selectolax/) -- version 0.4.6 verified (HIGH)
- [beautifulsoup4 PyPI](https://pypi.org/project/beautifulsoup4/) -- version 4.14.2 verified (HIGH)
- [Alembic PyPI](https://pypi.org/project/alembic/) -- version 1.18.3 verified (HIGH)
- [Resend Python SDK PyPI](https://pypi.org/project/resend/) -- version 2.21.0 verified (HIGH)
- [Resend Node SDK npm](https://www.npmjs.com/package/resend) -- version 6.9.1 verified (HIGH)
- [pytest PyPI](https://pypi.org/project/pytest/) -- version 9.0.2 verified (HIGH)
- [pytest-asyncio PyPI](https://pypi.org/project/pytest-asyncio/) -- version 1.3.0 verified (HIGH)
- [Vitest Releases](https://github.com/vitest-dev/vitest/releases) -- version 4.0.18 verified (HIGH)
- [Ruff GitHub](https://github.com/astral-sh/ruff) -- version 0.15.x verified (HIGH)
- [Biome GitHub](https://github.com/biomejs/biome) -- version 2.3.x verified (MEDIUM)
- [pnpm npm](https://www.npmjs.com/package/pnpm) -- version 10.28.x verified (HIGH)
- [uv Docs](https://docs.astral.sh/uv/) -- active development verified (HIGH)
- [Node.js Releases](https://nodejs.org/en/about/previous-releases) -- Node 22 LTS verified (HIGH)
- [asyncpg PyPI](https://pypi.org/project/asyncpg/) -- ~5x faster than psycopg3 (MEDIUM, benchmark from third-party)
- [Python 3.13 What's New](https://docs.python.org/3/whatsnew/3.13.html) -- features verified (HIGH)

---

*Stack research for: 5C Menu v2 — College dining menu app*
*Researched: 2026-02-07*
