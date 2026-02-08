"""Pomona dining hall parser (Frank, Frary, Oldenborg).

Fetches menu data via a two-step process: first discovers the JSON URL from the
Pomona menu page HTML, then fetches and parses the EatecExchange JSON feed.
Oldenborg items are split by comma AND slash; other halls by comma only.
"""

import json
import logging
import re
from datetime import date

import httpx
from selectolax.lexbor import LexborHTMLParser

from app.models.menu import ParsedMeal, ParsedMenu, ParsedMenuItem, ParsedStation
from app.parsers.base import BaseParser
from app.parsers.station_filters import (
    POMONA_FILTER,
    apply_station_filters,
    normalize_dietary_tags,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hall configuration
# ---------------------------------------------------------------------------

POMONA_HALLS: dict[str, dict[str, str]] = {
    "frank": {"name": "Frank", "slug": "frank"},
    "frary": {"name": "Frary", "slug": "frary"},
    "oldenborg": {"name": "Oldenborg", "slug": "oldenborg"},
}

_PAGE_URL_TEMPLATE = "https://www.pomona.edu/administration/dining/menus/{slug}"
_FALLBACK_JSON_URL_TEMPLATE = "https://my.pomona.edu/eatec/{name}.json"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class PomonaParser(BaseParser):
    """Parser for Pomona College dining halls.

    Supports Frank, Frary, and Oldenborg. Uses a two-step fetch: first
    fetches the Pomona menu page to discover the JSON URL via the
    ``data-dining-menu-json-url`` attribute, then fetches the JSON feed.
    """

    def __init__(self, hall_id: str, hall_name: str) -> None:
        if hall_id not in POMONA_HALLS:
            raise ValueError(
                f"Unknown Pomona hall: {hall_id!r}. "
                f"Must be one of {list(POMONA_HALLS)}"
            )
        super().__init__(hall_id, hall_name)
        self._hall_config = POMONA_HALLS[hall_id]

    def discover_json_url(self, page_html: str) -> str:
        """Extract the JSON URL from the Pomona menu page HTML.

        Looks for ``div#dining-menu-from-json`` and reads the
        ``data-dining-menu-json-url`` attribute. Falls back to the
        known eatec URL pattern if the attribute is not found.
        """
        tree = LexborHTMLParser(page_html)
        json_div = tree.css_first("#dining-menu-from-json")

        if json_div is not None:
            json_url = json_div.attributes.get("data-dining-menu-json-url")
            if json_url:
                return json_url

        # Fallback: try known URL pattern
        name = self._hall_config["name"]
        fallback_url = _FALLBACK_JSON_URL_TEMPLATE.format(name=name)
        logger.warning(
            "Could not find data-dining-menu-json-url for %s; "
            "falling back to %s",
            self.hall_id,
            fallback_url,
        )
        return fallback_url

    async def fetch_raw(self, target_date: date) -> str:
        """Two-step fetch: page HTML -> JSON URL -> JSON data."""
        slug = self._hall_config["slug"]
        page_url = _PAGE_URL_TEMPLATE.format(slug=slug)

        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; 5CMenu/1.0)"},
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            # Step 1: Fetch the menu page to discover JSON URL
            page_response = await client.get(page_url)
            page_response.raise_for_status()

            json_url = self.discover_json_url(page_response.text)

            # Step 2: Fetch the actual JSON data
            json_response = await client.get(json_url)
            json_response.raise_for_status()
            return json_response.text

    def parse(self, raw_content: str, target_date: date) -> ParsedMenu:
        """Parse EatecExchange JSON into structured menu data.

        Handles the single-item recipe edge case (dict instead of list),
        Oldenborg comma+slash splitting, dietary tag extraction, and
        station filtering.
        """
        data = json.loads(raw_content)
        menu_entries = data.get("EatecExchange", {}).get("menu", [])

        # Normalize to list (in case a single entry is returned as dict)
        if isinstance(menu_entries, dict):
            menu_entries = [menu_entries]

        target_str = target_date.strftime("%Y%m%d")
        meals_by_period: dict[str, list[ParsedStation]] = {}
        meal_order: list[str] = []

        for entry in menu_entries:
            serve_date = entry.get("@servedate", "")
            if serve_date != target_str:
                continue

            meal_period = entry.get("@mealperiodname", "")
            bulletin = entry.get("@menubulletin", "")

            # Skip closed meals
            if meal_period.lower() == "closed" or bulletin.lower() == "closed":
                continue

            if not meal_period:
                continue

            # Extract recipes -- handle single-item edge case
            recipes_container = entry.get("recipes", {})
            recipes = recipes_container.get("recipe", [])
            if isinstance(recipes, dict):
                recipes = [recipes]

            # Group items by station
            station_map: dict[str, list[ParsedMenuItem]] = {}
            station_order: list[str] = []

            for recipe in recipes:
                display = recipe.get("@displayonwebsite", "Y")
                if display != "Y":
                    continue

                raw_name = (recipe.get("@shortName") or "").strip()
                if not raw_name:
                    continue

                category = (recipe.get("@category") or "").strip()
                if not category:
                    category = "Miscellaneous"

                # Extract dietary tags
                tags = self._extract_dietary_tags(recipe)

                # Split item names
                item_names = self._split_item_name(raw_name)

                for item_name in item_names:
                    item_name = item_name.strip()
                    if not item_name:
                        continue

                    item = ParsedMenuItem(name=item_name, tags=tags)

                    cat_key = category.lower()
                    if cat_key not in station_map:
                        station_map[cat_key] = []
                        station_order.append(cat_key)
                    station_map[cat_key].append(item)

            # Build stations preserving insertion order
            stations: list[ParsedStation] = []
            for cat_key in station_order:
                # Find the original display name from the first recipe in this category
                display_name = category  # fallback
                for recipe in recipes:
                    if (recipe.get("@category") or "").strip().lower() == cat_key:
                        display_name = (recipe.get("@category") or "").strip()
                        break
                stations.append(
                    ParsedStation(name=display_name, items=station_map[cat_key])
                )

            # Apply station filters
            filtered = apply_station_filters(stations, POMONA_FILTER)

            meal_key = meal_period.lower()
            if meal_key in meals_by_period:
                # Merge stations into existing meal period
                meals_by_period[meal_key].extend(filtered)
            else:
                meals_by_period[meal_key] = list(filtered)
                meal_order.append(meal_key)

        # Build ParsedMeals
        meals: list[ParsedMeal] = []
        for meal_key in meal_order:
            stations = meals_by_period[meal_key]
            if stations:
                meals.append(ParsedMeal(meal=meal_key, stations=stations))

        return ParsedMenu(hall_id=self.hall_id, date=target_date, meals=meals)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_item_name(self, name: str) -> list[str]:
        """Split item names by comma (all halls) or comma+slash (Oldenborg).

        Only splits if the name actually contains the relevant delimiters.
        """
        if self.hall_id == "oldenborg":
            # Split by both comma and slash
            parts = re.split(r"[,/]\s*", name)
        else:
            # Split by comma only
            parts = name.split(",")

        # Strip whitespace and filter empty parts
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _extract_dietary_tags(recipe: dict) -> list[str]:
        """Extract dietary tags from a recipe's dietaryChoices field.

        Only includes tags where ``#text`` is ``"Yes"``. Normalizes
        via the shared DIETARY_TAG_MAP.
        """
        choices_container = recipe.get("dietaryChoices", {})
        if not choices_container:
            return []

        choices = choices_container.get("dietaryChoice", [])
        if isinstance(choices, dict):
            choices = [choices]

        raw_tags: list[str] = []
        for choice in choices:
            tag_value = choice.get("#text", "")
            if tag_value == "Yes":
                tag_id = choice.get("@id", "")
                if tag_id:
                    raw_tags.append(tag_id)

        return normalize_dietary_tags(raw_tags)
