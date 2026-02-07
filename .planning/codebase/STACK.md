# Technology Stack

**Analysis Date:** 2026-02-07

## Languages

**Primary:**
- Python 3 - Backend API (FastAPI)
- TypeScript - Web frontend (Next.js 14)
- TypeScript - Mobile frontend (Expo/React Native)
- JavaScript - Frontend runtime

**Secondary:**
- SQL - PostgreSQL database queries
- JSON - Configuration and data interchange (menu stations)

## Runtime

**Environment:**
- Python 3.x - Backend server runtime
- Node.js (LTS) - Frontend build and development
- Browser (web) - React frontend execution
- React Native runtime - Mobile app execution (via Expo managed service)

**Package Manager:**
- pip - Python dependencies
- npm or yarn - JavaScript/TypeScript dependencies
- Lockfile: Required for all (Pipfile.lock or requirements.txt for Python, package-lock.json or yarn.lock for Node.js)

## Frameworks

**Core:**
- FastAPI (Python) - Backend HTTP API framework with async support
- Next.js 14 (TypeScript/React) - Web frontend with App Router
- Expo (React Native) - Cross-platform mobile framework for iOS/Android
- Expo Router - Mobile app navigation layer

**Testing:**
- Not yet defined in PRD - to be determined during implementation

**Build/Dev:**
- Tailwind CSS - Web UI styling utility framework
- Vercel - Web frontend build and hosting platform
- Railway - Backend hosting and deployment platform

## Key Dependencies

**Critical:**
- FastAPI - REST API framework with request validation
- PostgreSQL driver (psycopg2 or asyncpg) - Database connectivity
- Redis client (redis-py) - Caching and session storage
- React Query (TanStack Query) - Data synchronization and caching (web + mobile)
- AsyncStorage (react-native-async-storage) - Mobile offline menu caching
- expo-location - Mobile location services integration with foreground-only capability

**Infrastructure:**
- SQLAlchemy (optional) - Python ORM for PostgreSQL models
- Pydantic - Python request/response validation in FastAPI
- Tailwind CSS - CSS utility framework for Next.js styling

## Configuration

**Environment:**
- Twelve-factor app approach implied (config via environment variables)
- Database connection string from environment variable
- Redis connection from environment variable
- API base URL configuration for frontend

**Build:**
- Vercel configuration for Next.js deployment (`vercel.json` or `next.config.js`)
- Railway configuration for FastAPI deployment (likely `Procfile` or `railway.toml`)
- Expo app configuration (`app.json` with Expo manifest)

## Platform Requirements

**Development:**
- Python 3.8+ with pip
- Node.js 18+ with npm/yarn
- PostgreSQL 12+ (local or managed)
- Redis 6+ (local or managed)
- Expo CLI for mobile development
- Xcode (macOS) for iOS simulator testing
- Android SDK/Emulator for Android testing

**Production:**
- **Backend:** Railway managed PostgreSQL + Railway-hosted FastAPI service
- **Frontend (Web):** Vercel hosted Next.js 14 deployment
- **Frontend (Mobile):** iOS App Store + Google Play Store via Expo EAS Build

---

*Stack analysis: 2026-02-07*
