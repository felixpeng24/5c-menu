"""Sodexo dining hall parser (Hoch-Shanahan).

Extracts menu data from JSON embedded in HTML (`#nutData` div).
Sodexo returns a week of data; we filter to the requested date.
"""

import json
import logging
import re
from datetime import date

import httpx
from selectolax.parser import HTMLParser

from app.models.menu import ParsedMeal, ParsedMenu, ParsedMenuItem, ParsedStation
from app.parsers.base import BaseParser
from app.parsers.station_filters import (
    DIETARY_TAG_MAP,
    SODEXO_FILTER,
    apply_station_filters,
    normalize_sodexo_station_name,
)

logger = logging.getLogger(__name__)

# Sodexo URL template -- menuId and locationId are for Hoch-Shanahan
_URL_TEMPLATE = (
    "https://menus.sodexomyway.com/BiteMenu/MenuOnly"
    "?menuId=15258&locationId=13147001&startdate={date}"
)


class SodexoParser(BaseParser):
    """Parser for Sodexo-powered dining halls (Hoch-Shanahan)."""

    def __init__(self, hall_id: str = "hoch", hall_name: str = "Hoch-Shanahan") -> None:
        super().__init__(hall_id, hall_name)

    def build_url(self, target_date: date) -> str:
        """Build Sodexo menu URL for the given date."""
        return _URL_TEMPLATE.format(date=target_date.strftime("%m/%d/%Y"))

    async def fetch_raw(self, target_date: date) -> str:
        """Fetch raw HTML from Sodexo menu page."""
        url = self.build_url(target_date)
        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; 5CMenu/1.0)"},
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def parse(self, raw_content: str, target_date: date) -> ParsedMenu:
        """Parse Sodexo HTML containing embedded JSON menu data.

        Extracts the JSON array from the ``#nutData`` div, filters to
        the requested date, and builds the ParsedMenu hierarchy with
        station filtering applied.
        """
        json_text = self._extract_json(raw_content)
        days = json.loads(json_text)

        target_str = target_date.isoformat()  # "YYYY-MM-DD"
        meals: list[ParsedMeal] = []

        for day in days:
            # Sodexo dates look like "2026-02-07T00:00:00"
            day_date_str = day.get("date", "")[:10]
            if day_date_str != target_str:
                continue

            for day_part in day.get("dayParts", []):
                meal = self._parse_day_part(day_part)
                if meal is not None:
                    meals.append(meal)

        return ParsedMenu(hall_id=self.hall_id, date=target_date, meals=meals)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(html: str) -> str:
        """Extract the JSON text from the #nutData div.

        Primary: selectolax CSS selector. Fallback: regex extraction.
        """
        # Primary: selectolax
        try:
            tree = HTMLParser(html)
            node = tree.css_first("#nutData")
            if node is not None:
                text = node.text().strip()
                if text:
                    return text
        except Exception:
            logger.debug("selectolax extraction failed, trying regex fallback")

        # Fallback: regex
        match = re.search(
            r'<div[^>]*id\s*=\s*["\']nutData["\'][^>]*>(.*?)</div>',
            html,
            re.DOTALL,
        )
        if match:
            text = match.group(1).strip()
            if text:
                return text

        raise ValueError(
            "Could not extract menu JSON from Sodexo HTML: "
            "#nutData div not found or empty"
        )

    def _parse_day_part(self, day_part: dict) -> ParsedMeal | None:
        """Parse a single dayPart (meal period) into a ParsedMeal."""
        meal_name = day_part.get("dayPartName", "").lower()
        if not meal_name:
            return None

        # Build stations, merging items into stations with the same
        # normalized name within this meal
        station_map: dict[str, ParsedStation] = {}
        station_order: list[str] = []

        for course in day_part.get("courses", []):
            raw_name = course.get("courseName", "")
            normalized = normalize_sodexo_station_name(raw_name)

            items = self._parse_items(course.get("menuItems", []))

            # Skip empty Miscellaneous stations (v1 behavior)
            if normalized == "Miscellaneous" and not items:
                continue

            key = normalized.lower()
            if key in station_map:
                existing = station_map[key]
                station_map[key] = ParsedStation(
                    name=existing.name,
                    items=existing.items + items,
                )
            else:
                station_map[key] = ParsedStation(name=normalized, items=items)
                station_order.append(key)

        stations = [station_map[k] for k in station_order]

        # Apply the full station filter pipeline
        filtered = apply_station_filters(stations, SODEXO_FILTER)

        if not filtered:
            return None

        return ParsedMeal(meal=meal_name, stations=filtered)

    @staticmethod
    def _parse_items(menu_items: list[dict]) -> list[ParsedMenuItem]:
        """Parse a list of Sodexo menuItems into ParsedMenuItems."""
        result: list[ParsedMenuItem] = []
        for item in menu_items:
            name = (item.get("formalName") or "").strip()
            if not name:
                continue

            # Extract dietary tags from boolean fields
            raw_tags: list[str] = []
            if item.get("isVegan"):
                raw_tags.append("isvegan")
            if item.get("isVegetarian"):
                raw_tags.append("isvegetarian")
            if item.get("isMindful"):
                raw_tags.append("ismindful")

            tags = sorted(
                {DIETARY_TAG_MAP[t] for t in raw_tags if t in DIETARY_TAG_MAP}
            )

            result.append(ParsedMenuItem(name=name, tags=tags))
        return result
