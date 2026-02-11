# 5C Menu

A dining hall menu aggregator for the Claremont Colleges. View what's being served across all seven dining halls, filter by meal period, check which halls are open right now, and browse menus up to a week ahead.

## Dining Halls

| Hall | College | Vendor |
|------|---------|--------|
| Hoch-Shanahan | Harvey Mudd | Sodexo |
| Collins | Claremont McKenna | Bon Appetit |
| Malott | Scripps | Bon Appetit |
| McConnell | Pitzer | Bon Appetit |
| Frank | Pomona | Pomona Dining |
| Frary | Pomona | Pomona Dining |
| Oldenborg | Pomona | Pomona Dining |

## Tech Stack

- **Backend:** FastAPI, SQLModel, PostgreSQL, Redis
- **Frontend:** Next.js 15, React 19, TanStack Query, Tailwind v4
- **Testing:** pytest (backend), Vitest (frontend)

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+

## Getting Started

### Backend

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"
pip install -r requirements.txt

# Set required environment variables
export FIVEC_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/fivec_menu"
export FIVEC_REDIS_URL="redis://localhost:6379/0"
export FIVEC_JWT_SECRET="your-secret-key"

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd web

# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the dev server
npm run dev
```

The frontend runs at `http://localhost:3000` and the API at `http://localhost:8000`.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIVEC_DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://localhost/fivec_menu` |
| `FIVEC_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `FIVEC_JWT_SECRET` | Secret key for admin session tokens | `dev-secret-change-me` |
| `FIVEC_TIMEZONE` | Timezone for open-now logic | `America/Los_Angeles` |
| `FIVEC_ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |
| `FIVEC_ADMIN_EMAIL` | Email address for admin magic links | &mdash; |
| `FIVEC_RESEND_API_KEY` | Resend API key for sending magic links | &mdash; |
| `FIVEC_FRONTEND_URL` | Frontend base URL for magic link generation | &mdash; |
| `NEXT_PUBLIC_API_URL` | Backend API URL (frontend) | &mdash; |

## Running Tests

```bash
# Backend (107 tests)
cd backend && pytest

# Frontend (17 tests)
cd web && npm run test:run
```

## Project Structure

```
5c-menu/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI application
│       ├── config.py         # Environment-based settings
│       ├── db.py             # Database init & hall seed data
│       ├── models/           # SQLModel ORM models
│       ├── parsers/          # Menu scrapers (Sodexo, Bon Appetit, Pomona)
│       ├── routers/          # API route handlers
│       ├── services/         # Business logic (caching, hours, auth)
│       └── schemas/          # Request/response schemas
├── web/
│   └── src/
│       ├── app/              # Next.js App Router pages
│       │   └── admin/        # Admin panel (hours, overrides, health)
│       ├── components/       # React components
│       └── lib/              # API clients, hooks, types, constants
└── mobile/                   # React Native app (planned)
```

## Architecture

Menu data flows through a cache-aside pipeline:

1. Frontend requests a menu via TanStack Query
2. API checks Redis cache (30-min jittered TTL)
3. On cache miss, the appropriate parser scrapes the vendor's site
4. Parsed menu is stored in PostgreSQL and cached in Redis
5. On parse failure, the last-known-good menu is returned from PostgreSQL with a stale indicator

Request coalescing prevents thundering herd on simultaneous cache misses. Jittered TTLs prevent synchronized cache expiration.

## API

All endpoints are under `/api/v2/`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/halls/` | List all dining halls |
| GET | `/menus/` | Get menu for a hall/date/meal |
| GET | `/open-now/` | Get halls currently open |
| POST | `/admin/auth/request-link` | Request admin magic link |
| POST | `/admin/auth/verify` | Verify magic link token |
| GET | `/admin/hours` | List dining hours |
| POST | `/admin/hours` | Create hours entry |
| PUT | `/admin/hours/{id}` | Update hours entry |
| DELETE | `/admin/hours/{id}` | Delete hours entry |
| GET | `/admin/overrides` | List holiday overrides |
| POST | `/admin/overrides` | Create override |
| PUT | `/admin/overrides/{id}` | Update override |
| DELETE | `/admin/overrides/{id}` | Delete override |
| GET | `/admin/health` | Parser health dashboard |

## License

MIT
