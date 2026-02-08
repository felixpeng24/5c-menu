"""Unit tests for the Sodexo (Hoch-Shanahan) parser.

All tests run against a saved HTML fixture -- zero network calls.
"""

from datetime import date
from pathlib import Path

import pytest

from app.models.menu import ParsedMenu, ParsedMenuItem, ParsedStation
from app.parsers.sodexo import SodexoParser
from app.parsers.station_filters import (
    SODEXO_FILTER,
    apply_station_filters,
    normalize_sodexo_station_name,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sodexo"
FIXTURE_DATE = date(2026, 2, 7)


@pytest.fixture
def fixture_html() -> str:
    """Load the saved Sodexo HTML fixture."""
    fixture_path = FIXTURE_DIR / "hoch_2026-02-07.html"
    return fixture_path.read_text()


@pytest.fixture
def parser() -> SodexoParser:
    """Create a SodexoParser instance for Hoch."""
    return SodexoParser("hoch", "Hoch-Shanahan")


@pytest.fixture
def parsed_menu(parser: SodexoParser, fixture_html: str) -> ParsedMenu:
    """Parse the fixture HTML into a ParsedMenu."""
    return parser.parse(fixture_html, FIXTURE_DATE)


# ------------------------------------------------------------------
# Test: parse returns valid menu structure
# ------------------------------------------------------------------


class TestSodexoParseReturnsMenu:
    def test_result_is_parsed_menu(self, parsed_menu: ParsedMenu) -> None:
        assert isinstance(parsed_menu, ParsedMenu)

    def test_hall_id(self, parsed_menu: ParsedMenu) -> None:
        assert parsed_menu.hall_id == "hoch"

    def test_date_matches(self, parsed_menu: ParsedMenu) -> None:
        assert parsed_menu.date == FIXTURE_DATE

    def test_at_least_one_meal(self, parsed_menu: ParsedMenu) -> None:
        assert len(parsed_menu.meals) >= 1


# ------------------------------------------------------------------
# Test: meals have stations with items
# ------------------------------------------------------------------


class TestSodexoMealsHaveStations:
    def test_each_meal_has_stations(self, parsed_menu: ParsedMenu) -> None:
        for meal in parsed_menu.meals:
            assert len(meal.stations) >= 1, f"{meal.meal} has no stations"

    def test_stations_have_items(self, parsed_menu: ParsedMenu) -> None:
        for meal in parsed_menu.meals:
            for station in meal.stations:
                assert len(station.items) >= 1, (
                    f"{meal.meal}/{station.name} has no items"
                )

    def test_item_names_are_nonempty(self, parsed_menu: ParsedMenu) -> None:
        for meal in parsed_menu.meals:
            for station in meal.stations:
                for item in station.items:
                    assert isinstance(item.name, str)
                    assert item.name.strip(), (
                        f"Empty item name in {meal.meal}/{station.name}"
                    )


# ------------------------------------------------------------------
# Test: hidden stations are removed
# ------------------------------------------------------------------


class TestSodexoHiddenStationsFiltered:
    def _all_station_names(self, parsed_menu: ParsedMenu) -> set[str]:
        names: set[str] = set()
        for meal in parsed_menu.meals:
            for station in meal.stations:
                names.add(station.name.lower())
        return names

    def test_no_hidden_stations(self, parsed_menu: ParsedMenu) -> None:
        names = self._all_station_names(parsed_menu)
        for hidden in SODEXO_FILTER.hidden:
            assert hidden not in names, f"Hidden station '{hidden}' was not filtered"

    def test_salad_bar_absent(self, parsed_menu: ParsedMenu) -> None:
        names = self._all_station_names(parsed_menu)
        assert "salad bar" not in names

    def test_deli_bar_absent(self, parsed_menu: ParsedMenu) -> None:
        names = self._all_station_names(parsed_menu)
        assert "deli bar" not in names

    def test_hot_cereal_absent(self, parsed_menu: ParsedMenu) -> None:
        names = self._all_station_names(parsed_menu)
        assert "hot cereal" not in names


# ------------------------------------------------------------------
# Test: station ordering matches v1
# ------------------------------------------------------------------


class TestSodexoStationOrdering:
    def test_ordered_stations_in_correct_relative_order(
        self, parsed_menu: ParsedMenu
    ) -> None:
        ordered_lower = [s.lower() for s in SODEXO_FILTER.ordered]
        order_map = {name: idx for idx, name in enumerate(ordered_lower)}

        for meal in parsed_menu.meals:
            if len(meal.stations) < 2:
                continue

            # Get the order indices of stations that appear in the ordered list
            indexed = [
                (order_map[s.name.lower()], s.name)
                for s in meal.stations
                if s.name.lower() in order_map
            ]
            if len(indexed) < 2:
                continue

            # They should be in ascending order
            for i in range(len(indexed) - 1):
                assert indexed[i][0] <= indexed[i + 1][0], (
                    f"In {meal.meal}: '{indexed[i][1]}' (order {indexed[i][0]}) "
                    f"should come before '{indexed[i + 1][1]}' (order {indexed[i + 1][0]})"
                )


# ------------------------------------------------------------------
# Test: truncation applied
# ------------------------------------------------------------------


class TestSodexoTruncation:
    def test_grill_truncated_to_3(self, parsed_menu: ParsedMenu) -> None:
        for meal in parsed_menu.meals:
            for station in meal.stations:
                if station.name.lower() == "grill":
                    assert len(station.items) <= 3, (
                        f"Grill in {meal.meal} has {len(station.items)} items, expected <= 3"
                    )

    def test_breakfast_truncated_to_12(self, parsed_menu: ParsedMenu) -> None:
        for meal in parsed_menu.meals:
            for station in meal.stations:
                if station.name.lower() == "breakfast":
                    assert len(station.items) <= 12, (
                        f"Breakfast in {meal.meal} has {len(station.items)} items, expected <= 12"
                    )


# ------------------------------------------------------------------
# Test: dietary tags extracted
# ------------------------------------------------------------------


class TestSodexoDietaryTags:
    CANONICAL_TAGS = {
        "vegan",
        "vegetarian",
        "mindful",
        "gluten-free",
        "halal",
        "balanced",
        "farm-to-fork",
        "humane",
    }

    def test_some_items_have_tags(self, parsed_menu: ParsedMenu) -> None:
        all_tags: set[str] = set()
        for meal in parsed_menu.meals:
            for station in meal.stations:
                for item in station.items:
                    all_tags.update(item.tags)
        assert len(all_tags) > 0, "No dietary tags found in any items"

    def test_all_tags_are_canonical(self, parsed_menu: ParsedMenu) -> None:
        for meal in parsed_menu.meals:
            for station in meal.stations:
                for item in station.items:
                    for tag in item.tags:
                        assert tag in self.CANONICAL_TAGS, (
                            f"Non-canonical tag '{tag}' in {item.name}"
                        )

    def test_vegetarian_tags_present(self, parsed_menu: ParsedMenu) -> None:
        all_tags: set[str] = set()
        for meal in parsed_menu.meals:
            for station in meal.stations:
                for item in station.items:
                    all_tags.update(item.tags)
        assert "vegetarian" in all_tags

    def test_vegan_tags_present(self, parsed_menu: ParsedMenu) -> None:
        all_tags: set[str] = set()
        for meal in parsed_menu.meals:
            for station in meal.stations:
                for item in station.items:
                    all_tags.update(item.tags)
        assert "vegan" in all_tags


# ------------------------------------------------------------------
# Test: station name normalization
# ------------------------------------------------------------------


class TestSodexoStationNameNormalization:
    def test_strips_scr_suffix(self) -> None:
        assert normalize_sodexo_station_name("EXHIBITION SCR") == "Exhibition"

    def test_title_cases_all_caps(self) -> None:
        assert normalize_sodexo_station_name("PASTA/NOODLES") == "Pasta/Noodles"

    def test_blank_to_miscellaneous(self) -> None:
        assert normalize_sodexo_station_name("  ") == "Miscellaneous"

    def test_dash_to_miscellaneous(self) -> None:
        assert normalize_sodexo_station_name("-") == "Miscellaneous"

    def test_preserves_mixed_case(self) -> None:
        assert normalize_sodexo_station_name("Chef's Corner") == "Chef's Corner"

    def test_fixes_and_word(self) -> None:
        assert normalize_sodexo_station_name("RICE AND BEANS") == "Rice and Beans"

    def test_fixes_hmc(self) -> None:
        assert normalize_sodexo_station_name("HMC SALAD") == "HMC Salad"


# ------------------------------------------------------------------
# Test: validate detects empty menu
# ------------------------------------------------------------------


class TestSodexoValidateEmpty:
    def test_empty_meals_returns_false(self, parser: SodexoParser) -> None:
        empty_menu = ParsedMenu(hall_id="hoch", date=FIXTURE_DATE, meals=[])
        assert parser.validate(empty_menu) is False

    def test_valid_menu_returns_true(
        self, parser: SodexoParser, parsed_menu: ParsedMenu
    ) -> None:
        assert parser.validate(parsed_menu) is True


# ------------------------------------------------------------------
# Test: combined stations are merged
# ------------------------------------------------------------------


class TestSodexoCombinedStations:
    def test_stew_and_soup_merge_to_soups(self) -> None:
        stations = [
            ParsedStation(
                name="Stew",
                items=[ParsedMenuItem(name="Beef Stew", tags=[])],
            ),
            ParsedStation(
                name="Soup",
                items=[ParsedMenuItem(name="Tomato Soup", tags=["vegan"])],
            ),
        ]
        filtered = apply_station_filters(stations, SODEXO_FILTER)
        soups = [s for s in filtered if s.name == "Soups"]
        assert len(soups) == 1
        assert len(soups[0].items) == 2
        names = {i.name for i in soups[0].items}
        assert "Beef Stew" in names
        assert "Tomato Soup" in names

    def test_alias_stations_merged_into_canonical(self) -> None:
        stations = [
            ParsedStation(
                name="hmc salad",
                items=[ParsedMenuItem(name="Caesar Salad", tags=[])],
            ),
            ParsedStation(
                name="special station salad north",
                items=[ParsedMenuItem(name="Greek Salad", tags=["vegetarian"])],
            ),
        ]
        filtered = apply_station_filters(stations, SODEXO_FILTER)
        merged = [s for s in filtered if s.name == "Special Salad Station"]
        assert len(merged) == 1
        assert len(merged[0].items) == 2


# ------------------------------------------------------------------
# Test: date filtering
# ------------------------------------------------------------------


class TestSodexoDateFiltering:
    def test_wrong_date_returns_empty_meals(
        self, parser: SodexoParser, fixture_html: str
    ) -> None:
        # Use a date not in the fixture week
        menu = parser.parse(fixture_html, date(2099, 1, 1))
        assert len(menu.meals) == 0

    def test_other_dates_in_week_work(
        self, parser: SodexoParser, fixture_html: str
    ) -> None:
        # Feb 3 is a weekday in the fixture week
        menu = parser.parse(fixture_html, date(2026, 2, 3))
        assert len(menu.meals) >= 1


# ------------------------------------------------------------------
# Test: build_url
# ------------------------------------------------------------------


class TestSodexoBuildUrl:
    def test_url_format(self, parser: SodexoParser) -> None:
        url = parser.build_url(date(2026, 2, 7))
        assert "02/07/2026" in url
        assert "menus.sodexomyway.com" in url

    def test_url_single_digit_month(self, parser: SodexoParser) -> None:
        url = parser.build_url(date(2026, 1, 5))
        assert "01/05/2026" in url
