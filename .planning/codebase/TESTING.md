# Testing Patterns

**Analysis Date:** 2026-02-07

## Overview

This is a monorepo with three independent codebases, each with its own testing framework and patterns. Test conventions are stack-specific.

---

## TypeScript Testing (Web & Mobile)

### Test Framework

**Runner:**
- Vitest (recommended for speed, not Jest)
- Config: `vitest.config.ts` in project root

**Assertion Library:**
- Vitest's built-in `expect()` (compatible with Jest)
- React Testing Library for component testing

**Run Commands:**
```bash
npm test                  # Run all tests
npm test -- --watch      # Watch mode
npm test -- --coverage   # Coverage report
npm test src/utils       # Run tests in specific directory
```

### Test File Organization

**Location:**
- Co-located with source code (same directory)
- Name pattern: `{filename}.test.ts` or `{filename}.test.tsx`

**Example structure:**
```
src/
├── components/
│   ├── DiningHallCard.tsx
│   ├── DiningHallCard.test.tsx
│   ├── CrowdingBadge.tsx
│   └── CrowdingBadge.test.tsx
├── utils/
│   ├── formatTime.ts
│   ├── formatTime.test.ts
│   ├── calculateCrowding.ts
│   └── calculateCrowding.test.ts
├── hooks/
│   ├── useLocation.ts
│   ├── useLocation.test.ts
│   ├── useMenus.ts
│   └── useMenus.test.ts
```

### Test Structure

**Suite Organization:**

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DiningHallCard } from "./DiningHallCard";

describe("DiningHallCard", () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
    vi.clearAllMocks();
  });

  it("should render hall name and crowding level", () => {
    const hall = { id: "collins", name: "Collins", college: "cmc" };
    render(<DiningHallCard hall={hall} />);

    expect(screen.getByText("Collins")).toBeInTheDocument();
    expect(screen.getByText("CMC")).toBeInTheDocument();
  });

  it("should call onSelect when clicked", async () => {
    const onSelect = vi.fn();
    const hall = { id: "collins", name: "Collins" };
    const { user } = render(<DiningHallCard hall={hall} onSelect={onSelect} />);

    await user.click(screen.getByRole("button"));

    expect(onSelect).toHaveBeenCalledWith("collins");
  });
});
```

**Patterns:**
- Describe blocks nest logically by component or function
- One assertion per test (or cohesive related assertions)
- Descriptive test names: `it("should X when Y")`
- Setup in `beforeEach`, cleanup in `afterEach`

### Mocking

**Framework:** Vitest's built-in `vi` module (compatible with Jest)

**Patterns:**

```typescript
// Mock modules
vi.mock("@/services/apiClient", () => ({
  apiClient: {
    getMenus: vi.fn(),
  },
}));

// Mock functions
const mockFetch = vi.fn().mockResolvedValue({ data: [] });

// Reset mocks
beforeEach(() => {
  vi.clearAllMocks();
});

// Assert on mock calls
expect(mockFetch).toHaveBeenCalledWith("collins", "2024-01-15");
expect(mockFetch).toHaveBeenCalledTimes(1);

// Mock React Query
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: mockData,
    isLoading: false,
    error: null,
  })),
}));
```

**What to Mock:**
- External API calls (services)
- React Query hooks
- Location APIs (`expo-location`)
- AsyncStorage (mobile)
- Date/time if testing time-dependent logic

**What NOT to Mock:**
- Component internals (test behavior, not implementation)
- Tailwind utilities
- Custom hooks (test them directly)
- Utility functions unless they're expensive (network, file I/O)

### Fixtures and Factories

**Test Data:**

```typescript
// src/testing/factories.ts
export function createDiningHall(overrides?: Partial<DiningHall>): DiningHall {
  return {
    id: "collins",
    name: "Collins Dining Hall",
    college: "cmc",
    color: "#3366CC",
    latitude: 34.1012,
    longitude: -117.7089,
    geofenceRadiusM: 50,
    ...overrides,
  };
}

export function createMenu(overrides?: Partial<Menu>): Menu {
  return {
    hallId: "collins",
    date: "2024-01-15",
    meal: "lunch",
    stations: [
      {
        name: "Grill",
        items: [
          { name: "Burger", tags: [] },
          { name: "Veggie Burger", tags: ["vegan"] },
        ],
      },
    ],
    ...overrides,
  };
}

// Usage in tests
it("should display vegan items", () => {
  const menu = createMenu({
    stations: [
      {
        name: "Vegan Station",
        items: [
          { name: "Tofu Stir-fry", tags: ["vegan"] },
        ],
      },
    ],
  });

  render(<MenuScreen menu={menu} />);
  expect(screen.getByText("Tofu Stir-fry")).toBeInTheDocument();
});
```

**Location:**
- `src/testing/factories.ts` for factory functions
- `src/testing/mocks.ts` for mock data and handlers
- `src/testing/setup.ts` for global setup (Vitest config)

### Coverage

**Requirements:**
- No minimum enforced in v1, but aim for 70%+ on critical paths
- Critical paths: API communication, crowding calculation, permission flows

**View Coverage:**
```bash
npm test -- --coverage
```

**Coverage report:**
- HTML report generated in `coverage/index.html`
- Console summary in test output

### Test Types

**Unit Tests:**
- Scope: Single function or component
- Approach: Test behavior with various inputs
- Use: Utilities (time formatting, crowding calculation), simple components

**Example:**
```typescript
// src/utils/calculateCrowding.test.ts
import { getCrowdingLevel } from "./calculateCrowding";

describe("getCrowdingLevel", () => {
  it("should return 'not_busy' when count < 15", () => {
    expect(getCrowdingLevel(10)).toBe("not_busy");
    expect(getCrowdingLevel(14)).toBe("not_busy");
  });

  it("should return 'moderate' when 15 <= count < 40", () => {
    expect(getCrowdingLevel(15)).toBe("moderate");
    expect(getCrowdingLevel(39)).toBe("moderate");
  });

  it("should return 'busy' when count >= 40", () => {
    expect(getCrowdingLevel(40)).toBe("busy");
    expect(getCrowdingLevel(100)).toBe("busy");
  });
});
```

**Integration Tests:**
- Scope: Multiple components or hooks working together
- Approach: Test user flows (fetch menu, display, navigate)
- Use: Hook composition, API integration, state updates

**Example:**
```typescript
// src/screens/MenuScreen.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MenuScreen } from "./MenuScreen";

vi.mock("@/services/apiClient", () => ({
  apiClient: {
    getMenus: vi.fn(),
  },
}));

describe("MenuScreen integration", () => {
  it("should fetch and display menus", async () => {
    const queryClient = new QueryClient();
    const mockMenus = [createMenu()];

    vi.mocked(apiClient.getMenus).mockResolvedValue(mockMenus);

    render(
      <QueryClientProvider client={queryClient}>
        <MenuScreen hallId="collins" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Collins Dining Hall")).toBeInTheDocument();
    });
  });
});
```

**E2E Tests:**
- Framework: Playwright or Cypress (recommended: Playwright)
- Scope: Full user flows (load app, navigate, interact)
- Location: `tests/e2e/`
- Not implemented in v1, but setup structure for future

### Common Patterns

**Async Testing:**

```typescript
// Using async/await
it("should fetch menus", async () => {
  const { result } = renderHook(() => useMenus("collins"));

  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
  });

  expect(result.current.data).toEqual(mockMenus);
});

// Using vi.waitFor
it("should update when data changes", async () => {
  const { rerender } = render(<Component value={1} />);

  rerender(<Component value={2} />);

  await waitFor(() => {
    expect(screen.getByText("2")).toBeInTheDocument();
  });
});
```

**Error Testing:**

```typescript
it("should display error when fetch fails", async () => {
  vi.mocked(apiClient.getMenus).mockRejectedValue(
    new Error("Network error"),
  );

  render(<MenuScreen hallId="collins" />);

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

**React Query Testing:**

```typescript
it("should use cached data on subsequent requests", async () => {
  const queryClient = new QueryClient();
  const mockFetch = vi.fn().mockResolvedValue(mockMenus);

  vi.mocked(apiClient.getMenus).mockImplementation(mockFetch);

  const { rerender } = render(
    <QueryClientProvider client={queryClient}>
      <MenuScreen hallId="collins" date="2024-01-15" />
    </QueryClientProvider>,
  );

  await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));

  rerender(
    <QueryClientProvider client={queryClient}>
      <MenuScreen hallId="collins" date="2024-01-15" />
    </QueryClientProvider>,
  );

  // Should not fetch again (cached)
  expect(mockFetch).toHaveBeenCalledTimes(1);
});
```

**Component Props Testing:**

```typescript
it("should apply conditional classes", () => {
  const { rerender } = render(
    <CrowdingBadge level="not_busy" />,
  );

  expect(screen.getByRole("badge")).toHaveClass("bg-green-100");

  rerender(<CrowdingBadge level="busy" />);

  expect(screen.getByRole("badge")).toHaveClass("bg-red-100");
});
```

### Vitest Configuration

**vitest.config.ts** (web example):

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/testing/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/",
        "src/testing/",
      ],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

**src/testing/setup.ts**:

```typescript
import { expect, afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock window.matchMedia for dark mode tests
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

---

## Python Testing (FastAPI Backend)

### Test Framework

**Runner:**
- pytest with pytest-asyncio for async tests
- Config: `pytest.ini` or `pyproject.toml` in project root

**Run Commands:**
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --watch                  # Watch mode (requires pytest-watch)
pytest --cov=app                # Coverage report
pytest tests/test_menu_parser.py # Run specific file
pytest -k "test_fetch"          # Run tests matching pattern
```

### Test File Organization

**Location:**
- Separate `tests/` directory at project root
- Structure mirrors `app/` directory
- Name pattern: `test_{module_name}.py`

**Example structure:**
```
tests/
├── test_models.py
├── test_api_endpoints.py
├── test_menu_parser.py
├── services/
│   ├── test_hall_service.py
│   ├── test_menu_service.py
│   └── test_crowding_service.py
├── parsers/
│   ├── test_sodexo_parser.py
│   ├── test_bon_appetit_parser.py
│   └── test_pomona_parser.py
└── conftest.py  # Shared fixtures
```

### Test Structure

**Suite Organization:**

```python
import pytest
from app.services.menu_service import get_menus
from app.models import DiningHall

class TestGetMenus:
    """Menu fetching functionality."""

    @pytest.fixture
    def setup(self, db_session):
        """Setup test data."""
        hall = DiningHall(
            id="collins",
            name="Collins",
            college="cmc",
            latitude=34.1012,
            longitude=-117.7089,
        )
        db_session.add(hall)
        db_session.commit()
        return hall

    def test_fetch_menu_success(self, setup, db_session):
        """Should fetch menu when data exists."""
        hall = setup
        menus = get_menus(db_session, hall.id, "2024-01-15")

        assert len(menus) > 0
        assert menus[0].hall_id == "collins"

    def test_fetch_menu_not_found(self, db_session):
        """Should return empty list when menu not found."""
        menus = get_menus(db_session, "nonexistent", "2024-01-15")

        assert menus == []

    @pytest.mark.asyncio
    async def test_fetch_menu_with_parser(self, setup, db_session, mocker):
        """Should fetch and cache menu."""
        mocker.patch("app.services.menu_service.parser.fetch", return_value=[])

        menus = await get_menus(db_session, setup.id, "2024-01-15")

        assert isinstance(menus, list)
```

**Patterns:**
- Group related tests in test classes
- One assertion per test (or logically related assertions)
- Descriptive function names: `test_should_X_when_Y`
- Use fixtures for setup, clean database state between tests

### Mocking

**Framework:** pytest-mock (provides `mocker` fixture)

**Patterns:**

```python
# Mock functions
def test_parser_fallback(mocker):
    mock_parser = mocker.patch("app.parsers.sodexo.fetch")
    mock_parser.side_effect = NetworkError("Connection failed")
    mock_cache = mocker.patch("app.cache.get", return_value=cached_data)

    result = get_menus("collins", "2024-01-15")

    assert result == cached_data
    mock_parser.assert_called_once()

# Mock external services
def test_redis_connection(mocker):
    mock_redis = mocker.MagicMock()
    mock_redis.get.return_value = b'{"level": "busy"}'

    mocker.patch("app.cache.redis", mock_redis)

    level = get_crowding("collins")

    assert level == "busy"

# Mock with side effects
def test_rate_limit(mocker):
    mock_time = mocker.patch("time.time")
    mock_time.side_effect = [0, 1, 2]  # Simulate time progression

    # Test logic...

# Reset mocks
mocker.resetall()
```

**What to Mock:**
- External API calls (Sodexo, Bon Appétit websites)
- Redis operations
- Database calls (use fixtures instead in most cases)
- HTTP requests
- Time/datetime if testing time-dependent logic

**What NOT to Mock:**
- Pydantic models
- Utility functions
- Core business logic (test it directly)
- Database (use fixtures with test DB instead)

### Fixtures and Factories

**Test Data:**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, DiningHall, Menu

@pytest.fixture(scope="session")
def db_engine():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    """Provide test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_hall(db_session):
    """Create sample dining hall."""
    hall = DiningHall(
        id="collins",
        name="Collins Dining Hall",
        college="cmc",
        latitude=34.1012,
        longitude=-117.7089,
        geofence_radius_m=50,
    )
    db_session.add(hall)
    db_session.commit()
    return hall

def create_menu_data(**kwargs) -> dict:
    """Factory for menu data."""
    defaults = {
        "hall_id": "collins",
        "date": "2024-01-15",
        "meal": "lunch",
        "stations": [
            {
                "name": "Grill",
                "items": [
                    {"name": "Burger", "tags": []},
                    {"name": "Veggie Burger", "tags": ["vegan"]},
                ],
            },
        ],
    }
    return {**defaults, **kwargs}

# Usage in tests
def test_menu_display(db_session):
    menu_data = create_menu_data(meal="dinner")

    # Test with menu_data...
```

### Coverage

**Requirements:**
- Aim for 80%+ on critical paths (parsers, crowding logic, API endpoints)
- 60%+ overall coverage in v1

**View Coverage:**
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

### Test Types

**Unit Tests:**
- Scope: Single function or service method
- Approach: Test with various inputs and error conditions
- Use: Parsers, utilities, business logic

**Example:**
```python
# tests/test_crowding_calculator.py
import pytest
from app.services.crowding import get_crowding_level, estimate_crowding

class TestCrowdingCalculation:
    def test_crowding_level_not_busy(self):
        """Count < 15 is not busy."""
        assert get_crowding_level(10) == "not_busy"
        assert get_crowding_level(14) == "not_busy"

    def test_crowding_level_moderate(self):
        """15 <= count < 40 is moderate."""
        assert get_crowding_level(15) == "moderate"
        assert get_crowding_level(39) == "moderate"

    def test_crowding_level_busy(self):
        """Count >= 40 is busy."""
        assert get_crowding_level(40) == "busy"
        assert get_crowding_level(100) == "busy"

    def test_estimate_crowding_peak_time(self, sample_hall):
        """Peak time (middle of meal) should be busy."""
        from datetime import datetime, time, timedelta

        current_time = datetime(2024, 1, 15, 12, 30)  # Noon
        meal_start = time(11, 0)
        meal_end = time(13, 0)

        level = estimate_crowding(
            sample_hall.id,
            current_time,
            meal_start,
            meal_end,
        )

        assert level == "busy"

    def test_estimate_crowding_off_peak(self, sample_hall):
        """Early morning should be not busy."""
        from datetime import datetime, time

        current_time = datetime(2024, 1, 15, 11, 5)  # Early
        meal_start = time(11, 0)
        meal_end = time(13, 0)

        level = estimate_crowding(
            sample_hall.id,
            current_time,
            meal_start,
            meal_end,
        )

        assert level == "not_busy"
```

**Integration Tests:**
- Scope: API endpoint + service + database
- Approach: Test full request/response cycle
- Use: HTTP endpoints, error responses, caching

**Example:**
```python
# tests/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestMenuEndpoints:
    def test_get_menus_success(self, sample_hall, db_session):
        """GET /menus should return menu list."""
        response = client.get(
            "/api/v2/menus",
            params={"hall": "collins", "date": "2024-01-15"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_menus_not_found(self):
        """GET /menus with invalid date should return empty."""
        response = client.get(
            "/api/v2/menus",
            params={"hall": "collins", "date": "1900-01-01"},
        )

        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_get_crowding_includes_all_halls(self, db_session):
        """GET /crowding should include all halls."""
        response = client.get("/api/v2/crowding")

        assert response.status_code == 200
        data = response.json()["data"]
        hall_ids = {c["hall_id"] for c in data}
        expected_ids = {"collins", "hoch", "malott", "mcconnell", "frank", "frary", "oldenborg"}
        assert expected_ids.issubset(hall_ids)
```

### Common Patterns

**Async Testing:**

```python
@pytest.mark.asyncio
async def test_async_fetch():
    """Test async function."""
    result = await async_menu_fetch("collins")

    assert isinstance(result, list)

# Or with fixture scope
@pytest.fixture
def async_client(app):
    """Async test client for FastAPI."""
    from httpx import AsyncClient
    return AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_with_async_client(async_client):
    response = await async_client.get("/api/v2/halls")
    assert response.status_code == 200
```

**Error Testing:**

```python
def test_invalid_coordinates(mocker):
    """Should reject out-of-bounds coordinates."""
    mocker.patch("app.validation.is_in_bounds", return_value=False)

    with pytest.raises(ValidationError):
        validate_location(50.0, 180.0)  # Out of bounds

def test_api_error_response(client, mocker):
    """API should return proper error on parser failure."""
    mocker.patch(
        "app.parsers.get_parser",
        side_effect=ExternalAPIError("Server error"),
    )

    response = client.get("/api/v2/menus?hall=collins&date=2024-01-15")

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["error"]
```

**Database Transaction Testing:**

```python
def test_location_ping_persists(db_session, sample_hall):
    """Location ping should be stored in Redis."""
    ping_data = {
        "session_id": "test-uuid",
        "latitude": 34.1012,
        "longitude": -117.7089,
        "timestamp": "2024-01-15T12:30:00Z",
    }

    store_location_ping(ping_data)
    stored = retrieve_location_ping("test-uuid")

    assert stored is not None
    assert stored["session_id"] == "test-uuid"
```

### pytest Configuration

**pytest.ini** or section in **pyproject.toml**:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --disable-warnings
markers =
    asyncio: marks tests as async (deselect with '-m "not asyncio"')
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
asyncio_mode = auto
```

---

## Coverage Goals by Component

| Component | Target | Rationale |
|-----------|--------|-----------|
| Menu parsers | 85%+ | Core functionality, web scraping is fragile |
| Crowding logic | 90%+ | Business-critical, multiple edge cases |
| API endpoints | 80%+ | Public interface, error handling |
| Utilities | 75%+ | Nice-to-have, obvious from usage |
| Components | 70%+ | UI testing is slower, focus on behavior |
| Services | 80%+ | Data transformation and API calls |

---

*Testing analysis: 2026-02-07*
