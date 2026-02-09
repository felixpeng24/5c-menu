import datetime as _dt
from datetime import date

import pytest
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.dependencies import get_redis, get_session
from app.main import app
from app.models.dining_hall import DiningHall
from app.models.dining_hours import DiningHours, DiningHoursOverride
from app.models.menu import (
    Menu,
    ParsedMeal,
    ParsedMenu,
    ParsedMenuItem,
    ParsedStation,
)


# ---------------------------------------------------------------------------
# Phase 1 fixtures (preserved from original conftest)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_menu_item():
    """A single parsed menu item."""
    return ParsedMenuItem(name="Grilled Chicken", tags=["gluten-free"])


@pytest.fixture
def sample_station(sample_menu_item):
    """A parsed station with one item."""
    return ParsedStation(name="Exhibition", items=[sample_menu_item])


@pytest.fixture
def sample_meal(sample_station):
    """A parsed meal with one station."""
    return ParsedMeal(meal="lunch", stations=[sample_station])


@pytest.fixture
def sample_parsed_menu(sample_meal):
    """A complete parsed menu for testing."""
    return ParsedMenu(
        hall_id="hoch",
        date=date(2026, 2, 7),
        meals=[sample_meal],
    )


@pytest.fixture
def make_parsed_menu():
    """Factory fixture for creating ParsedMenu instances with custom data."""

    def _make(
        hall_id: str = "hoch",
        target_date: date = date(2026, 2, 7),
        meals: list[dict] | None = None,
    ) -> ParsedMenu:
        if meals is None:
            meals = [
                {
                    "meal": "lunch",
                    "stations": [
                        {
                            "name": "Exhibition",
                            "items": [
                                {"name": "Grilled Chicken", "tags": ["gluten-free"]},
                                {"name": "Veggie Burger", "tags": ["vegan"]},
                            ],
                        },
                        {
                            "name": "Grill",
                            "items": [
                                {"name": "Hamburger", "tags": []},
                            ],
                        },
                    ],
                }
            ]

        parsed_meals = []
        for m in meals:
            stations = [
                ParsedStation(
                    name=s["name"],
                    items=[ParsedMenuItem(**i) for i in s["items"]],
                )
                for s in m["stations"]
            ]
            parsed_meals.append(ParsedMeal(meal=m["meal"], stations=stations))

        return ParsedMenu(hall_id=hall_id, date=target_date, meals=parsed_meals)

    return _make


# ---------------------------------------------------------------------------
# Phase 2 integration-test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_engine():
    """In-memory async SQLite engine with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Async database session bound to the in-memory SQLite engine."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def fake_redis():
    """FakeAsyncRedis instance for cache testing without a real Redis server."""
    r = FakeAsyncRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
async def seed_halls(test_session):
    """Insert all 7 dining halls into the test database."""
    halls = [
        DiningHall(id="hoch", name="Hoch-Shanahan", college="hmc", vendor_type="sodexo", color="#F5C518"),
        DiningHall(id="collins", name="Collins", college="cmc", vendor_type="bonappetit", color="#800000"),
        DiningHall(id="malott", name="Malott", college="scripps", vendor_type="bonappetit", color="#2E4057"),
        DiningHall(id="mcconnell", name="McConnell", college="pitzer", vendor_type="bonappetit", color="#FF6600"),
        DiningHall(id="frank", name="Frank", college="pomona", vendor_type="bonappetit", color="#003B5C"),
        DiningHall(id="frary", name="Frary", college="pomona", vendor_type="bonappetit", color="#003B5C"),
        DiningHall(id="oldenborg", name="Oldenborg", college="pomona", vendor_type="bonappetit", color="#003B5C"),
    ]
    for hall in halls:
        test_session.add(hall)
    await test_session.commit()
    return halls


@pytest.fixture
async def seed_hours(test_session, seed_halls):
    """Insert dining hours for hoch and collins on Monday (day_of_week=1)."""
    hours = [
        # Hoch: lunch 11:00-13:30, dinner 17:00-20:00
        DiningHours(
            hall_id="hoch", day_of_week=1, meal="lunch",
            start_time=_dt.time(11, 0), end_time=_dt.time(13, 30),
        ),
        DiningHours(
            hall_id="hoch", day_of_week=1, meal="dinner",
            start_time=_dt.time(17, 0), end_time=_dt.time(20, 0),
        ),
        # Collins: lunch 11:30-13:30, dinner 17:00-19:30
        DiningHours(
            hall_id="collins", day_of_week=1, meal="lunch",
            start_time=_dt.time(11, 30), end_time=_dt.time(13, 30),
        ),
        DiningHours(
            hall_id="collins", day_of_week=1, meal="dinner",
            start_time=_dt.time(17, 0), end_time=_dt.time(19, 30),
        ),
    ]
    for h in hours:
        test_session.add(h)
    await test_session.commit()
    return hours


@pytest.fixture
async def seed_menu(test_session, seed_halls):
    """Insert a menu row for hoch/today/lunch with sample stations."""
    today = _dt.date.today()
    menu = Menu(
        hall_id="hoch",
        date=today,
        meal="lunch",
        stations_json=[
            {
                "name": "Exhibition",
                "items": [{"name": "Grilled Chicken", "tags": ["gluten-free"]}],
            },
            {
                "name": "Grill",
                "items": [{"name": "Hamburger", "tags": []}],
            },
        ],
        fetched_at=_dt.datetime.now(_dt.timezone.utc),
        is_valid=True,
    )
    test_session.add(menu)
    await test_session.commit()
    return menu


@pytest.fixture
async def client(test_session, fake_redis):
    """Async HTTP client with dependency overrides for session and redis."""

    async def _override_session():
        yield test_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
