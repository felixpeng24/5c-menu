# Coding Conventions

**Analysis Date:** 2026-02-07

## Project Overview

This is a monorepo containing three independent codebases:
- **Backend**: Python/FastAPI in `backend/`
- **Web Frontend**: Next.js (React/TypeScript) in `web/`
- **Mobile**: Expo/React Native (TypeScript) in `mobile/`

Conventions are language-specific.

---

## TypeScript (Web & Mobile)

### Naming Patterns

**Files:**
- Components: PascalCase in `src/components/` (e.g., `DiningHallCard.tsx`, `CrowdingBadge.tsx`)
- Pages/Screens: PascalCase matching route structure in `src/app/` or `src/screens/`
- Utilities: camelCase in `src/utils/` (e.g., `formatTime.ts`, `calculateCrowding.ts`)
- Hooks: PascalCase with `use` prefix in `src/hooks/` (e.g., `useLocation.ts`, `useMenus.ts`)
- Services: camelCase in `src/services/` (e.g., `apiClient.ts`, `storageManager.ts`)
- Types: PascalCase in `src/types/` (e.g., `DiningHall.ts`, `Menu.ts`)
- Constants: camelCase in `src/constants/` (e.g., `apiEndpoints.ts`, `geofences.ts`)

**Functions:**
- camelCase: `getUserLocation()`, `fetchMenus()`, `calculateBusiness()`
- Handlers: `handle` prefix for event handlers: `handleLocationPermission()`, `handleDayChange()`

**Variables:**
- camelCase: `currentHall`, `isLoading`, `menuData`
- Constants: UPPER_SNAKE_CASE: `MAX_REQUESTS_PER_MINUTE`, `SESSION_TTL_SECONDS`
- Boolean flags: `is` or `has` prefix: `isLoading`, `hasPermission`, `hasError`

**Types:**
- PascalCase: `type DiningHall = {}`, `interface CrowdingLevel {}`
- Props: `{Component}Props` (e.g., `MenuCardProps`, `CrowdingBadgeProps`)

### Code Style

**Formatting:**
- Prettier is used for formatting (configured in project root)
- Line length: 100 characters
- Tab width: 2 spaces
- Trailing commas: all
- Single quotes: false (use double quotes)

**Linting:**
- ESLint configured with React/Next.js rules
- Key rules enforced:
  - No unused variables (`@typescript-eslint/no-unused-vars`)
  - No console logs in production code (flag warnings)
  - Prefer `const` over `let` over `var`
  - No any types (`@typescript-eslint/no-explicit-any`)
  - Exhaustive dependency arrays in hooks

### Import Organization

**Order (ascending specificity):**
1. Node.js built-in modules: `import fs from "fs"`
2. External packages: `import React from "react"`, `import { useQuery } from "@tanstack/react-query"`
3. Type imports: `import type { DiningHall } from "@/types"`
4. Relative imports: `import { apiClient } from "../../services"`
5. Barrel file imports: `import { Button, Card } from "@/ui"`

**Path Aliases:**
- `@/` = project root (`src/` for web/mobile)
- Use absolute paths with aliases, not relative paths beyond 2 levels
- Avoid `../../../../../../` patterns

**Example:**
```typescript
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { DiningHall, Menu } from "@/types";
import { apiClient } from "@/services/apiClient";
import { DiningHallCard } from "@/components/DiningHallCard";
import { GEOFENCES } from "@/constants/geofences";
```

### Error Handling

**Patterns:**
- Use explicit error types, not generic `Error`
- Wrap API calls in try-catch: log error, return fallback or throw to caller
- API errors trigger user-facing messages (Toasts, inline error text)
- Never log sensitive data (location, session IDs, API keys)

**Example:**
```typescript
async function fetchMenus(hallId: string, date: string) {
  try {
    const data = await apiClient.get(`/menus?hall=${hallId}&date=${date}`);
    return data;
  } catch (error) {
    if (error instanceof NetworkError) {
      return getCachedMenus(hallId, date) || [];
    }
    throw error;
  }
}
```

### Logging

**Framework:** Console (no external logger in v1)

**Patterns:**
- Development: Use `console.log()` for debugging, wrapped in `if (process.env.NODE_ENV === "development")`
- Production: Minimal logging, only errors via error boundaries / Sentry (future)
- Never log: user data, location, session IDs, API keys

**Example:**
```typescript
if (process.env.NODE_ENV === "development") {
  console.log(`Fetched ${menus.length} items for hall ${hallId}`);
}
```

### Comments

**When to Comment:**
- Complex business logic (crowding threshold calculations, geofence logic)
- Non-obvious workarounds or hacks (flag as `// TODO:` or `// HACK:`)
- Public API documentation (JSDoc)

**No Comments Needed For:**
- Self-explanatory code (clear function/variable names)
- Loop or conditional logic in simple functions
- Props and return types (use TypeScript types instead)

**JSDoc/TSDoc:**
- Document public functions and components
- Include parameter types, return type, and purpose

**Example:**
```typescript
/**
 * Calculate crowding level based on active session count.
 * @param count - Number of active sessions in geofence
 * @returns Crowding level: "not_busy" | "moderate" | "busy"
 */
function getCrowdingLevel(count: number): CrowdingLevel {
  if (count < 15) return "not_busy";
  if (count < 40) return "moderate";
  return "busy";
}
```

### Function Design

**Size:** Keep functions under 50 lines. Break into smaller functions if exceeding.

**Parameters:** Max 3-4 parameters. Use object destructuring for more:
```typescript
// Good
function fetchMenu({ hallId, date, includeCache }: FetchMenuOptions) {}

// Avoid
function fetchMenu(hallId: string, date: string, something: boolean, another: string) {}
```

**Return Values:** Explicit return types, avoid implicit `any` or `unknown`:
```typescript
function getMenus(hallId: string): Menu[] | null {
  // ...
}
```

### Module Design

**Exports:**
- Named exports for functions/components that might be reused
- Default exports for page/screen components
- Co-locate related functions in a single file, separate by concern (services, components, utils)

**Barrel Files:**
- Use in `src/ui/`, `src/components/` for convenience
- Don't use in feature directories (encourages circular dependencies)

**Example:**
```typescript
// src/ui/index.ts
export { Button } from "./Button";
export { Card } from "./Card";
export { Badge } from "./Badge";

// Usage
import { Button, Card, Badge } from "@/ui";
```

### React-Specific Conventions

**Components:**
- Functional components only (no class components)
- Prop destructuring in signature: `function Button({ label, onClick }: ButtonProps) {}`
- Hooks at top of component, before JSX

**Hooks:**
- Custom hooks in `src/hooks/` with `use` prefix
- Exhaustive dependency arrays
- Hook rules enforced by ESLint

**State Management (React Query):**
- `useQuery()` for data fetching (menus, crowding data)
- Cache time: 5 minutes for stable data (menus), 30 seconds for crowding
- Stale time: 2 minutes for menus
- Use `enabled` flag to conditionally fetch

**Example:**
```typescript
function MenuScreen({ hallId }: MenuScreenProps) {
  const [selectedDate, setSelectedDate] = useState(new Date());

  const { data: menus, isLoading } = useQuery({
    queryKey: ["menus", hallId, selectedDate.toISOString()],
    queryFn: () => apiClient.getMenus(hallId, selectedDate),
    staleTime: 2 * 60 * 1000,
  });

  if (isLoading) return <LoadingSpinner />;
  return <MenuList menus={menus || []} />;
}
```

### Styling (Tailwind CSS)

**Convention:**
- Use Tailwind utility classes exclusively (no custom CSS unless necessary)
- Organize classes logically: layout → sizing → spacing → colors → effects
- Use `cn()` utility for conditional classes (from `clsx` or similar)

**Example:**
```typescript
<div className={cn(
  "flex items-center gap-2 rounded-lg border",
  isActive && "border-blue-500 bg-blue-50",
  isDark && "border-gray-700 bg-gray-900",
)}>
  <span className="text-sm font-medium">{label}</span>
</div>
```

---

## Python (FastAPI Backend)

### Naming Patterns

**Files:**
- Modules: snake_case in `src/` (e.g., `menu_parser.py`, `crowding_service.py`)
- Classes: PascalCase (e.g., `SodexoParser`, `CrowdingAggregator`)
- Functions: snake_case (e.g., `fetch_menus()`, `calculate_crowding()`)

**Variables:**
- snake_case: `current_hall`, `is_loading`, `menu_data`
- Constants: UPPER_SNAKE_CASE: `MAX_REQUESTS_PER_MINUTE`, `GEOFENCE_RADIUS_M`
- Boolean flags: `is_` or `has_` prefix: `is_loading`, `has_permission`

**Types:**
- PascalCase for Pydantic models: `class DiningHall(BaseModel)`, `class Menu(BaseModel)`

### Code Style

**Formatting:**
- Black is used for code formatting
- Line length: 100 characters
- Use type hints on all functions and variables

**Linting:**
- Ruff for linting (fast, Python 3.10+ compatible)
- Key rules:
  - No unused imports
  - No unused variables
  - Prefer f-strings for formatting

### Import Organization

**Order (ascending specificity):**
1. Standard library: `import os`, `import json`
2. Third-party packages: `from fastapi import FastAPI`, `from sqlalchemy import Column`
3. Local imports: `from app.models import DiningHall`, `from app.services import menu_parser`

**Example:**
```python
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, String, Integer
from pydantic import BaseModel

from app.models import DiningHall
from app.services.menu_parser import SodexoParser
```

### Error Handling

**Patterns:**
- Raise `HTTPException` for API errors (400, 404, 500)
- Catch specific exceptions, not generic `Exception`
- Log errors with context (not sensitive data like location)
- Return meaningful error messages to client

**Example:**
```python
@app.get("/menus/{hall_id}")
async def get_menus(hall_id: str, date: str) -> list[MenuItem]:
    try:
        menus = await menu_service.fetch(hall_id, date)
        if not menus:
            raise HTTPException(
                status_code=404,
                detail=f"No menu found for {hall_id} on {date}",
            )
        return menus
    except ExternalAPIError as e:
        logger.error(f"Parser error for {hall_id}: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

### Logging

**Framework:** Python `logging` module (stdlib)

**Patterns:**
- Configure root logger in `main.py`
- Use `logging.getLogger(__name__)` in each module
- Log levels: DEBUG (dev), INFO (normal), WARNING (issues), ERROR (failures)
- Never log: location coordinates, session IDs, API keys, user data

**Example:**
```python
import logging

logger = logging.getLogger(__name__)

def fetch_menus(hall_id: str):
    logger.info(f"Fetching menus for hall: {hall_id}")
    try:
        data = parser.fetch(hall_id)
        logger.debug(f"Fetched {len(data)} items")
        return data
    except NetworkError:
        logger.error(f"Network error fetching {hall_id}")
        raise
```

### Comments

**When to Comment:**
- Complex algorithms (geofence distance calculation, crowding aggregation)
- Non-obvious business logic (schedule-based estimation, fallback conditions)
- Workarounds or hacks (flag as `# TODO:` or `# HACK:`)

**No Comments Needed For:**
- Clear, self-explanatory code
- Standard library functions
- Variable assignments with clear names

**Docstrings:**
- Use triple-quoted docstrings for functions and classes (Google style)
- Include parameters, return type, and purpose

**Example:**
```python
def estimate_crowding(hall_id: str, current_time: datetime) -> str:
    """
    Estimate crowding based on meal window heuristic.

    Args:
        hall_id: Dining hall identifier
        current_time: Current time

    Returns:
        Crowding level: "not_busy", "moderate", or "busy"
    """
    meal = get_current_meal(hall_id, current_time)
    if not meal:
        return "not_busy"

    # Calculate position within meal window (0.0 to 1.0)
    position = (current_time - meal.start_time) / (meal.end_time - meal.start_time)
    peak_factor = 1 - abs(position - 0.5) * 2

    if peak_factor > 0.6:
        return "busy"
    elif peak_factor > 0.3:
        return "moderate"
    return "not_busy"
```

### Function Design

**Size:** Keep functions under 50 lines. Break into smaller functions if exceeding.

**Parameters:** Use keyword-only arguments for clarity in API functions:
```python
async def get_crowding(
    *,
    hall_id: Optional[str] = None,
    include_estimated: bool = False,
) -> dict:
    """Get crowding data."""
```

**Return Types:** Always annotate return types:
```python
def get_hall(hall_id: str) -> Optional[DiningHall]:
    """Fetch dining hall by ID."""
```

### Pydantic Models

**Patterns:**
- Define models in `app/models.py` or feature-specific modules
- Use field validation with `Field()` for constraints
- Use `Config` class for serialization settings

**Example:**
```python
from pydantic import BaseModel, Field

class LocationPing(BaseModel):
    session_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "uuid-here",
                "latitude": 34.1061,
                "longitude": -117.7117,
                "timestamp": "2024-01-15T12:30:00Z",
            }
        }
```

### Database & ORM (SQLAlchemy)

**Patterns:**
- Define models in `app/models.py`
- Use `async` sessions with `AsyncSession`
- Separate database layer (queries) from service layer (business logic)

**Example:**
```python
# app/models.py
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DiningHall(Base):
    __tablename__ = "dining_halls"

    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    college = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

# app/services/hall_service.py
async def get_hall(session: AsyncSession, hall_id: str) -> Optional[DiningHall]:
    result = await session.execute(
        select(DiningHall).where(DiningHall.id == hall_id)
    )
    return result.scalars().first()
```

---

## Shared Patterns (Both Stacks)

### API Communication

**Endpoint Naming:**
- Resource-based: `/api/v2/halls`, `/api/v2/menus`, `/api/v2/crowding`
- Query parameters for filtering: `/api/v2/menus?hall=collins&date=2024-01-15`
- No verb-based endpoints: avoid `/api/v2/getHall` or `/api/v2/fetchMenus`

**Response Format:**
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2024-01-15T12:30:00Z"
}
```

### Environment Variables

**Naming:** UPPER_SNAKE_CASE, prefixed by service:
- `DATABASE_URL`
- `REDIS_URL`
- `ADMIN_PASSWORD`
- `API_BASE_URL` (frontend)

**Never hardcode:** URLs, keys, passwords, environment-specific settings.

### Date/Time Handling

**Format:** ISO 8601 (RFC 3339)
- Serialization: `"2024-01-15T12:30:00Z"`
- Internal representation: Native language types (Python `datetime`, JS `Date`)
- Always use UTC, never local time for storage

### Sensitive Data

**Never log/store:**
- Location coordinates
- Session IDs
- API keys
- User device information
- IP addresses (analytics only, PII-safe)

---

## Monorepo Organization

**Directory structure follows each tech stack's conventions:**
- `backend/` - Python FastAPI (Django-like structure)
- `web/` - Next.js app router (T3 Stack inspired)
- `mobile/` - Expo/React Native (React Native conventions)

**No shared code between stacks** (different languages). Each codebase is independent.

---

*Convention analysis: 2026-02-07*
