"""Unit tests for the Pomona dining hall parser.

All tests run against saved fixture files -- no network calls.
"""

import json
from datetime import date
from pathlib import Path

import pytest
from selectolax.lexbor import LexborHTMLParser

from app.models.menu import ParsedMenu
from app.parsers.pomona import PomonaParser
from app.parsers.station_filters import POMONA_FILTER

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pomona"
TARGET_DATE = date(2026, 2, 7)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def frank_json() -> str:
    return (FIXTURES_DIR / "frank_2026-02-07.json").read_text()


@pytest.fixture
def frary_json() -> str:
    return (FIXTURES_DIR / "frary_2026-02-07.json").read_text()


@pytest.fixture
def oldenborg_json() -> str:
    return (FIXTURES_DIR / "oldenborg_2026-02-07.json").read_text()


@pytest.fixture
def frank_page_html() -> str:
    return (FIXTURES_DIR / "frank_page.html").read_text()


@pytest.fixture
def frank_parser() -> PomonaParser:
    return PomonaParser("frank", "Frank")


@pytest.fixture
def frary_parser() -> PomonaParser:
    return PomonaParser("frary", "Frary")


@pytest.fixture
def oldenborg_parser() -> PomonaParser:
    return PomonaParser("oldenborg", "Oldenborg")


def _make_synthetic_json(
    serve_date: str = "20260207",
    meal_period: str = "Lunch",
    bulletin: str = "",
    recipes: list | dict | None = None,
) -> str:
    """Build a minimal EatecExchange JSON string for testing."""
    if recipes is None:
        recipes = [
            {
                "@category": "Entree",
                "@shortName": "Test Item",
                "@displayonwebsite": "Y",
                "dietaryChoices": {"dietaryChoice": []},
            }
        ]

    entry: dict = {
        "@servedate": serve_date,
        "@mealperiodname": meal_period,
        "@menubulletin": bulletin,
        "recipes": {"recipe": recipes},
    }

    return json.dumps({"EatecExchange": {"menu": [entry]}})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pomona_parse_returns_menu(frank_parser: PomonaParser, frank_json: str) -> None:
    """Parsing Frank fixture returns a ParsedMenu with at least 1 meal."""
    menu = frank_parser.parse(frank_json, TARGET_DATE)
    assert isinstance(menu, ParsedMenu)
    assert len(menu.meals) >= 1
    assert menu.hall_id == "frank"
    assert menu.date == TARGET_DATE


def test_pomona_all_halls_parse(
    frank_parser: PomonaParser,
    frary_parser: PomonaParser,
    oldenborg_parser: PomonaParser,
    frank_json: str,
    frary_json: str,
    oldenborg_json: str,
) -> None:
    """All 3 Pomona halls produce valid menus from their fixtures."""
    for parser, fixture in [
        (frank_parser, frank_json),
        (frary_parser, frary_json),
        (oldenborg_parser, oldenborg_json),
    ]:
        menu = parser.parse(fixture, TARGET_DATE)
        assert isinstance(menu, ParsedMenu)
        assert len(menu.meals) >= 1, f"{parser.hall_id} should have at least 1 meal"


def test_pomona_meals_have_stations(
    frank_parser: PomonaParser, frank_json: str
) -> None:
    """Frank fixture meals have stations with items."""
    menu = frank_parser.parse(frank_json, TARGET_DATE)
    for meal in menu.meals:
        assert len(meal.stations) >= 1, f"{meal.meal} should have stations"
        for station in meal.stations:
            assert len(station.items) >= 1, (
                f"{meal.meal}/{station.name} should have items"
            )


def test_pomona_single_item_recipe(frank_parser: PomonaParser) -> None:
    """Single-item recipe (dict not list) is handled without crashing."""
    single_recipe = {
        "@category": "Entree",
        "@shortName": "Solo Dish",
        "@displayonwebsite": "Y",
        "dietaryChoices": {
            "dietaryChoice": [
                {"@id": "Vegetarian", "#text": "Yes"},
            ]
        },
    }
    raw = _make_synthetic_json(recipes=single_recipe)
    menu = frank_parser.parse(raw, TARGET_DATE)
    assert len(menu.meals) == 1
    all_items = [
        item
        for station in menu.meals[0].stations
        for item in station.items
    ]
    assert len(all_items) == 1
    assert all_items[0].name == "Solo Dish"
    assert "vegetarian" in all_items[0].tags


def test_pomona_single_item_recipe_frary(
    frary_parser: PomonaParser, frary_json: str
) -> None:
    """Frary Dinner fixture has a single recipe as dict -- verify it parses."""
    menu = frary_parser.parse(frary_json, TARGET_DATE)
    dinner_meals = [m for m in menu.meals if m.meal == "dinner"]
    assert len(dinner_meals) == 1
    dinner = dinner_meals[0]
    all_items = [
        item for station in dinner.stations for item in station.items
    ]
    assert len(all_items) >= 1
    assert any(item.name == "Lamb Stew" for item in all_items)


def test_pomona_oldenborg_splitting(
    oldenborg_parser: PomonaParser, oldenborg_json: str
) -> None:
    """Oldenborg splits item names by comma AND slash."""
    menu = oldenborg_parser.parse(oldenborg_json, TARGET_DATE)
    all_items = [
        item.name
        for meal in menu.meals
        for station in meal.stations
        for item in station.items
    ]
    # "Pasta/Salad, Bread" should become 3 items
    assert "Pasta" in all_items
    assert "Salad" in all_items
    assert "Bread" in all_items
    # "Baklava/Flan" should become 2 items
    assert "Baklava" in all_items
    assert "Flan" in all_items


def test_pomona_frank_comma_only_split(frank_parser: PomonaParser) -> None:
    """Non-Oldenborg halls split by comma only, not slash."""
    raw = _make_synthetic_json(
        recipes=[
            {
                "@category": "Entree",
                "@shortName": "Pasta/Salad, Bread",
                "@displayonwebsite": "Y",
                "dietaryChoices": {"dietaryChoice": []},
            }
        ]
    )
    menu = frank_parser.parse(raw, TARGET_DATE)
    all_items = [
        item.name
        for meal in menu.meals
        for station in meal.stations
        for item in station.items
    ]
    # Comma split only: "Pasta/Salad" and "Bread"
    assert "Pasta/Salad" in all_items
    assert "Bread" in all_items
    assert "Pasta" not in all_items  # Should NOT be split by slash
    assert "Salad" not in all_items


def test_pomona_station_ordering(
    frank_parser: PomonaParser, frank_json: str
) -> None:
    """Stations are ordered according to POMONA_FILTER.ordered."""
    menu = frank_parser.parse(frank_json, TARGET_DATE)
    lunch_meals = [m for m in menu.meals if m.meal == "lunch"]
    assert len(lunch_meals) == 1
    lunch = lunch_meals[0]

    station_names_lower = [s.name.lower() for s in lunch.stations]
    ordered_lower = [s.lower() for s in POMONA_FILTER.ordered]

    # Verify that stations present in the ordered list appear in the correct
    # relative order
    ordered_positions = []
    for name in station_names_lower:
        if name in ordered_lower:
            ordered_positions.append(ordered_lower.index(name))

    assert ordered_positions == sorted(ordered_positions), (
        f"Station ordering violated: {station_names_lower}"
    )


def test_pomona_dietary_tags(
    frank_parser: PomonaParser, frank_json: str
) -> None:
    """Dietary tags are extracted where #text == 'Yes' and normalized."""
    menu = frank_parser.parse(frank_json, TARGET_DATE)

    # Find an item we know has tags (Scrambled Eggs: Vegetarian=Yes, Gluten Free=Yes)
    all_items_with_tags = [
        item
        for meal in menu.meals
        for station in meal.stations
        for item in station.items
        if item.tags
    ]
    assert len(all_items_with_tags) > 0, "Should have items with dietary tags"

    # Check tag normalization: should use lowercase canonical strings
    for item in all_items_with_tags:
        for tag in item.tags:
            assert tag == tag.lower(), f"Tag {tag!r} should be lowercase"
            assert tag in {
                "vegan", "vegetarian", "gluten-free", "halal",
                "mindful", "balanced", "farm-to-fork", "humane",
            }, f"Unknown tag: {tag!r}"

    # Verify specific item
    scrambled = None
    for meal in menu.meals:
        for station in meal.stations:
            for item in station.items:
                if item.name == "Scrambled Eggs":
                    scrambled = item
                    break
    assert scrambled is not None
    assert "vegetarian" in scrambled.tags
    assert "gluten-free" in scrambled.tags
    assert "vegan" not in scrambled.tags  # Vegan=No for this item


def test_pomona_closed_skipped(frank_parser: PomonaParser) -> None:
    """Closed meal periods are excluded from the parsed menu."""
    raw = json.dumps({
        "EatecExchange": {
            "menu": [
                {
                    "@servedate": "20260207",
                    "@mealperiodname": "Closed",
                    "@menubulletin": "Closed",
                    "recipes": {"recipe": []},
                },
                {
                    "@servedate": "20260207",
                    "@mealperiodname": "Dinner",
                    "@menubulletin": "Closed",
                    "recipes": {
                        "recipe": [
                            {
                                "@category": "Entree",
                                "@shortName": "Should Not Appear",
                                "@displayonwebsite": "Y",
                                "dietaryChoices": {"dietaryChoice": []},
                            }
                        ]
                    },
                },
            ]
        }
    })
    menu = frank_parser.parse(raw, TARGET_DATE)
    assert len(menu.meals) == 0, "Closed meals should not appear"


def test_pomona_json_url_discovery(
    frank_parser: PomonaParser, frank_page_html: str
) -> None:
    """JSON URL is discovered from the page HTML data attribute."""
    url = frank_parser.discover_json_url(frank_page_html)
    assert url is not None
    assert "eatec/Frank.json" in url


def test_pomona_json_url_discovery_fallback() -> None:
    """When the data attribute is missing, falls back to known URL pattern."""
    parser = PomonaParser("frary", "Frary")
    html = "<html><body><div>No menu div here</div></body></html>"
    url = parser.discover_json_url(html)
    assert "eatec/Frary.json" in url


def test_pomona_wrong_date_returns_empty(frank_parser: PomonaParser) -> None:
    """Parsing for a date not in the fixture returns empty meals."""
    raw = _make_synthetic_json(serve_date="20260301")
    menu = frank_parser.parse(raw, TARGET_DATE)
    assert len(menu.meals) == 0


def test_pomona_displayonwebsite_n_filtered(frank_parser: PomonaParser) -> None:
    """Items with @displayonwebsite=N are filtered out."""
    raw = _make_synthetic_json(
        recipes=[
            {
                "@category": "Entree",
                "@shortName": "Visible Item",
                "@displayonwebsite": "Y",
                "dietaryChoices": {"dietaryChoice": []},
            },
            {
                "@category": "Entree",
                "@shortName": "Hidden Item",
                "@displayonwebsite": "N",
                "dietaryChoices": {"dietaryChoice": []},
            },
        ]
    )
    menu = frank_parser.parse(raw, TARGET_DATE)
    all_names = [
        item.name
        for meal in menu.meals
        for station in meal.stations
        for item in station.items
    ]
    assert "Visible Item" in all_names
    assert "Hidden Item" not in all_names


def test_pomona_invalid_hall_id() -> None:
    """Creating a parser with an invalid hall_id raises ValueError."""
    with pytest.raises(ValueError, match="Unknown Pomona hall"):
        PomonaParser("invalid", "Invalid")
