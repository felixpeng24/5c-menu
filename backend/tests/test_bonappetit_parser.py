"""Unit tests for the Bon Appetit (BAMCO) parser.

All tests run against saved HTML fixtures or synthetic HTML fragments --
no network calls are made.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from app.models.menu import ParsedMenu
from app.parsers.bonappetit import (
    BAMCO_HALLS,
    BonAppetitParser,
    _clean_station_label,
)
from app.parsers.station_filters import BONAPPETIT_FILTER, DIETARY_TAG_MAP

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bonappetit"
TARGET_DATE = date(2026, 2, 7)

# Canonical dietary tags that normalize_dietary_tags can produce
CANONICAL_TAGS = set(DIETARY_TAG_MAP.values())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def collins_html() -> str:
    return (FIXTURES_DIR / "collins_2026-02-07.html").read_text()


@pytest.fixture
def malott_html() -> str:
    return (FIXTURES_DIR / "malott_2026-02-07.html").read_text()


@pytest.fixture
def mcconnell_html() -> str:
    return (FIXTURES_DIR / "mcconnell_2026-02-07.html").read_text()


@pytest.fixture
def collins_parser() -> BonAppetitParser:
    return BonAppetitParser("collins", "Collins")


@pytest.fixture
def malott_parser() -> BonAppetitParser:
    return BonAppetitParser("malott", "Malott")


@pytest.fixture
def mcconnell_parser() -> BonAppetitParser:
    return BonAppetitParser("mcconnell", "McConnell")


def _make_synthetic_html(
    menu_items: dict,
    dayparts: dict[str, dict],
) -> str:
    """Build a minimal HTML page with embedded Bamco JS objects."""
    lines = ["<html><body><script>"]
    lines.append(f"Bamco.menu_items = {json.dumps(menu_items)};")
    for dp_id, dp_data in dayparts.items():
        lines.append(f"Bamco.dayparts['{dp_id}'] = {json.dumps(dp_data)};")
    lines.append("</script></body></html>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBamcoRegexExtraction:
    """Test that regex extraction of Bamco objects works."""

    def test_bamco_regex_extraction(self, collins_parser, collins_html):
        """Parse Collins fixture and verify basic structure."""
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        assert isinstance(menu, ParsedMenu)
        assert len(menu.meals) >= 1
        assert menu.hall_id == "collins"

    def test_bamco_regex_extraction_missing_menu_items(self, collins_parser):
        """Raise ValueError when Bamco.menu_items is not found."""
        with pytest.raises(ValueError, match="Bamco.menu_items"):
            collins_parser.parse("<html></html>", TARGET_DATE)

    def test_bamco_regex_extraction_missing_dayparts(self, collins_parser):
        """Raise ValueError when Bamco.dayparts is not found."""
        html = '<html><script>Bamco.menu_items = {"1": {"id": "1"}};</script></html>'
        with pytest.raises(ValueError, match="Bamco.dayparts"):
            collins_parser.parse(html, TARGET_DATE)


class TestBamcoAllHalls:
    """Test that all 3 BAMCO halls parse successfully."""

    def test_bamco_all_halls_parse(
        self,
        collins_parser,
        malott_parser,
        mcconnell_parser,
        collins_html,
        malott_html,
        mcconnell_html,
    ):
        halls = [
            (collins_parser, collins_html, "collins"),
            (malott_parser, malott_html, "malott"),
            (mcconnell_parser, mcconnell_html, "mcconnell"),
        ]
        for parser, html, hall_id in halls:
            menu = parser.parse(html, TARGET_DATE)
            assert isinstance(menu, ParsedMenu), f"{hall_id}: not a ParsedMenu"
            assert len(menu.meals) >= 1, f"{hall_id}: no meals"
            assert menu.hall_id == hall_id

    def test_bamco_invalid_hall_id(self):
        """Reject unknown hall IDs."""
        with pytest.raises(ValueError, match="Unknown BAMCO hall"):
            BonAppetitParser("fake_hall", "Fake")


class TestBamcoMealsAndStations:
    """Test that parsed meals contain stations with items."""

    def test_bamco_meals_have_stations(self, collins_parser, collins_html):
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        for meal in menu.meals:
            assert len(meal.stations) > 0, f"Meal {meal.meal} has no stations"
            for station in meal.stations:
                assert len(station.items) > 0, (
                    f"Station {station.name} in {meal.meal} has no items"
                )
                for item in station.items:
                    assert item.name, "Item has empty name"


class TestBamcoSpecialFiltering:
    """Test that only items with special=truthy are included."""

    def test_bamco_special_filtering(self, collins_parser):
        """Items with special=false must be excluded from output."""
        menu_items = {
            "100": {
                "id": "100",
                "label": "Served Today Chicken",
                "special": 1,
                "cor_icon": {},
                "station_id": "1",
                "station": "grill",
            },
            "200": {
                "id": "200",
                "label": "Not Served Pasta",
                "special": 0,
                "cor_icon": {},
                "station_id": "1",
                "station": "grill",
            },
            "300": {
                "id": "300",
                "label": "Also Served Salad",
                "special": 1,
                "cor_icon": {"1": "Vegan"},
                "station_id": "1",
                "station": "grill",
            },
        }
        dayparts = {
            "1": {
                "id": "1",
                "label": "Lunch",
                "stations": [
                    {
                        "order_id": "1",
                        "id": "1",
                        "label": "main plate",
                        "items": ["100", "200", "300"],
                    }
                ],
            }
        }
        html = _make_synthetic_html(menu_items, dayparts)
        menu = collins_parser.parse(html, TARGET_DATE)

        all_item_names = []
        for meal in menu.meals:
            for station in meal.stations:
                all_item_names.extend(item.name for item in station.items)

        assert "Served Today Chicken" in all_item_names
        assert "Also Served Salad" in all_item_names
        assert "Not Served Pasta" not in all_item_names

    def test_bamco_special_false_excluded_from_fixture(
        self, collins_parser, collins_html
    ):
        """Verify fixture parsing excludes non-special items.

        The Collins fixture has many items with special=0 -- none should
        appear in the parsed output.
        """
        import re

        # Count items with special=0 in raw data
        match = re.search(r"Bamco\.menu_items\s*=\s*(\{[^;]+\});", collins_html)
        raw_items = json.loads(match.group(1))
        non_special_labels = {
            v["label"].lower()
            for v in raw_items.values()
            if not v.get("special")
        }

        # Parse and collect all output item names
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        output_labels = set()
        for meal in menu.meals:
            for station in meal.stations:
                for item in station.items:
                    output_labels.add(item.name.lower())

        # No non-special items should appear in output
        overlap = non_special_labels & output_labels
        assert not overlap, f"Non-special items found in output: {overlap}"


class TestBamcoStationFiltering:
    """Test station filtering (hidden, ordered, truncated)."""

    def test_bamco_hidden_stations_filtered(self, collins_parser, collins_html):
        """Hidden stations from BONAPPETIT_FILTER must not appear."""
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        hidden_set = set(BONAPPETIT_FILTER.hidden)
        for meal in menu.meals:
            for station in meal.stations:
                assert station.name.lower() not in hidden_set, (
                    f"Hidden station {station.name!r} found in {meal.meal}"
                )

    def test_bamco_station_ordering(self, collins_parser, collins_html):
        """Stations in BONAPPETIT_FILTER.ordered appear in correct relative order."""
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        ordered_lower = [s.lower() for s in BONAPPETIT_FILTER.ordered]

        for meal in menu.meals:
            if len(meal.stations) < 2:
                continue
            station_names = [s.name.lower() for s in meal.stations]
            # Get positions in the ordered list for stations that appear there
            positions = []
            for name in station_names:
                if name in ordered_lower:
                    positions.append(ordered_lower.index(name))
            # Positions should be monotonically non-decreasing
            assert positions == sorted(positions), (
                f"Station order wrong in {meal.meal}: "
                f"names={station_names}, positions={positions}"
            )

    def test_bamco_truncation(self, collins_parser, collins_html):
        """Truncated stations should respect item limits."""
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        for meal in menu.meals:
            for station in meal.stations:
                lower_name = station.name.lower()
                limit = BONAPPETIT_FILTER.truncated.get(lower_name)
                if limit is not None and limit > 0:
                    assert len(station.items) <= limit, (
                        f"Station {station.name!r} in {meal.meal} has "
                        f"{len(station.items)} items, limit is {limit}"
                    )


class TestBamcoDietaryTags:
    """Test dietary tag extraction from cor_icon."""

    def test_bamco_dietary_tags(self, collins_parser, collins_html):
        """Items should have dietary tags from cor_icon, all canonical."""
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        all_tags: set[str] = set()
        items_with_tags = 0
        for meal in menu.meals:
            for station in meal.stations:
                for item in station.items:
                    if item.tags:
                        items_with_tags += 1
                        all_tags.update(item.tags)

        assert items_with_tags > 0, "No items have dietary tags"
        for tag in all_tags:
            assert tag in CANONICAL_TAGS, f"Non-canonical tag: {tag!r}"

    def test_bamco_dietary_tags_from_synthetic(self, collins_parser):
        """Verify specific cor_icon values produce correct canonical tags."""
        menu_items = {
            "1": {
                "id": "1",
                "label": "Vegan Bowl",
                "special": 1,
                "cor_icon": {
                    "1": "Vegan",
                    "9": "Made without Gluten-Containing Ingredients",
                },
            },
            "2": {
                "id": "2",
                "label": "Pasta",
                "special": 1,
                "cor_icon": {"1": "Vegetarian", "2": "In Balance"},
            },
        }
        dayparts = {
            "1": {
                "id": "1",
                "label": "Lunch",
                "stations": [
                    {"order_id": "1", "id": "1", "label": "main plate", "items": ["1", "2"]},
                ],
            }
        }
        html = _make_synthetic_html(menu_items, dayparts)
        menu = collins_parser.parse(html, TARGET_DATE)

        items = menu.meals[0].stations[0].items
        vegan_item = next(i for i in items if i.name == "Vegan Bowl")
        pasta_item = next(i for i in items if i.name == "Pasta")

        assert "vegan" in vegan_item.tags
        assert "gluten-free" in vegan_item.tags
        assert "vegetarian" in pasta_item.tags
        assert "balanced" in pasta_item.tags


class TestBamcoLabelCleaning:
    """Test HTML and @ stripping from station labels."""

    def test_bamco_station_label_cleaning_html(self, collins_parser):
        """HTML tags should be stripped from station labels."""
        menu_items = {
            "1": {
                "id": "1",
                "label": "Tofu",
                "special": 1,
                "cor_icon": {},
            },
        }
        dayparts = {
            "1": {
                "id": "1",
                "label": "Dinner",
                "stations": [
                    {
                        "order_id": "1",
                        "id": "1",
                        "label": "<strong>@herbivore</strong>",
                        "items": ["1"],
                    }
                ],
            }
        }
        html = _make_synthetic_html(menu_items, dayparts)
        menu = collins_parser.parse(html, TARGET_DATE)
        station_names = [s.name for m in menu.meals for s in m.stations]
        assert "herbivore" in station_names
        # Ensure no HTML or @ in station names
        for name in station_names:
            assert "<" not in name
            assert ">" not in name
            assert not name.startswith("@")

    def test_clean_station_label_function(self):
        """Direct tests of the _clean_station_label helper."""
        assert _clean_station_label("<strong>@herbivore</strong>") == "herbivore"
        assert _clean_station_label("@home") == "home"
        assert _clean_station_label("breakfast @ home") == "breakfast @ home"
        assert _clean_station_label("<em>expo</em>") == "expo"
        assert _clean_station_label("grill") == "grill"
        assert _clean_station_label("  @vegan  ") == "vegan"


class TestBamcoDuplicateItems:
    """Test deduplication of items within a station."""

    def test_bamco_duplicate_items(self, collins_parser):
        """Duplicate items (same label) within a station should be deduplicated."""
        menu_items = {
            "1": {
                "id": "1",
                "label": "Grilled Chicken",
                "special": 1,
                "cor_icon": {},
            },
            "2": {
                "id": "2",
                "label": "Grilled Chicken",
                "special": 1,
                "cor_icon": {"1": "Vegan"},
            },
            "3": {
                "id": "3",
                "label": "Rice Bowl",
                "special": 1,
                "cor_icon": {},
            },
        }
        dayparts = {
            "1": {
                "id": "1",
                "label": "Lunch",
                "stations": [
                    {
                        "order_id": "1",
                        "id": "1",
                        "label": "main plate",
                        "items": ["1", "2", "3"],
                    }
                ],
            }
        }
        html = _make_synthetic_html(menu_items, dayparts)
        menu = collins_parser.parse(html, TARGET_DATE)

        items = menu.meals[0].stations[0].items
        names = [i.name for i in items]
        assert names.count("Grilled Chicken") == 1, (
            f"Expected 1 'Grilled Chicken', got {names.count('Grilled Chicken')}"
        )
        assert "Rice Bowl" in names


class TestBamcoTruncation:
    """Test truncation limits on specific stations."""

    def test_bamco_truncation_applied(self, collins_parser, collins_html):
        """Stations with truncation limits should respect those limits."""
        menu = collins_parser.parse(collins_html, TARGET_DATE)
        for meal in menu.meals:
            for station in meal.stations:
                lower = station.name.lower()
                # Check truncation for stations whose name directly matches
                # a key in the truncated config (after the combine step,
                # "grill" becomes "grill special" so it won't match "grill")
                limit = BONAPPETIT_FILTER.truncated.get(lower)
                if limit is not None and limit > 0:
                    assert len(station.items) <= limit, (
                        f"Station {station.name!r} in {meal.meal} has "
                        f"{len(station.items)} items, limit is {limit}"
                    )

    def test_bamco_truncation_synthetic(self, collins_parser):
        """Verify truncation with a synthetic fixture using a truncated station name."""
        # "breakfast @home" has a truncation limit of 3
        items = {}
        item_ids = []
        for i in range(10):
            iid = str(100 + i)
            items[iid] = {
                "id": iid,
                "label": f"Item {i}",
                "special": 1,
                "cor_icon": {},
            }
            item_ids.append(iid)

        dayparts = {
            "1": {
                "id": "1",
                "label": "Breakfast",
                "stations": [
                    {
                        "order_id": "1",
                        "id": "1",
                        "label": "breakfast @home",
                        "items": item_ids,
                    }
                ],
            }
        }
        html = _make_synthetic_html(items, dayparts)
        menu = collins_parser.parse(html, TARGET_DATE)

        limit = BONAPPETIT_FILTER.truncated.get("breakfast @home")
        assert limit is not None and limit > 0
        # Find the station (after cleaning, "breakfast @home" stays as-is
        # since @ is not at the start)
        for meal in menu.meals:
            for station in meal.stations:
                if "home" in station.name.lower():
                    assert len(station.items) <= limit, (
                        f"Station {station.name!r} has {len(station.items)} "
                        f"items, expected <= {limit}"
                    )


class TestBamcoBuildUrl:
    """Test URL building."""

    def test_build_url_format(self):
        parser = BonAppetitParser("collins", "Collins")
        url = parser.build_url(date(2026, 2, 7))
        assert url == "https://collins-cmc.cafebonappetit.com/cafe/collins/2026-02-07"

    def test_build_url_all_halls(self):
        for hall_id, config in BAMCO_HALLS.items():
            parser = BonAppetitParser(hall_id, config["name"])
            url = parser.build_url(date(2026, 3, 15))
            assert "2026-03-15" in url
