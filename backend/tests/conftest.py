from datetime import date

import pytest

from app.models.menu import ParsedMenu, ParsedMeal, ParsedStation, ParsedMenuItem


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
