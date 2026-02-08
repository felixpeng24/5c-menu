"""Bon Appetit (BAMCO) parser for Collins, Malott, and McConnell dining halls.

Extracts menu data from inline JavaScript objects (Bamco.menu_items and
Bamco.dayparts) embedded in the cafe pages via regex.
"""

import json
import logging
import re
from datetime import date

import httpx

from app.models.menu import ParsedMeal, ParsedMenu, ParsedMenuItem, ParsedStation
from app.parsers.base import BaseParser
from app.parsers.station_filters import (
    BONAPPETIT_FILTER,
    apply_station_filters,
    normalize_dietary_tags,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hall configuration
# ---------------------------------------------------------------------------

BAMCO_HALLS: dict[str, dict[str, str]] = {
    "collins": {
        "name": "Collins",
        "url": "https://collins-cmc.cafebonappetit.com/cafe/collins/{date}",
    },
    "malott": {
        "name": "Malott",
        "url": "https://scripps.cafebonappetit.com/cafe/malott-dining-commons/{date}",
    },
    "mcconnell": {
        "name": "McConnell",
        "url": "https://pitzer.cafebonappetit.com/cafe/mcconnell-bistro/{date}",
    },
}

# ---------------------------------------------------------------------------
# Regex patterns for JavaScript object extraction
# ---------------------------------------------------------------------------

RE_MENU_ITEMS = re.compile(r"Bamco\.menu_items\s*=\s*(\{[^;]+\});")
RE_DAYPARTS = re.compile(r"Bamco\.dayparts\[\'(\d+)\'\]\s*=\s*(\{[^;]+\});")
RE_HTML_TAGS = re.compile(r"<[^>]+>")


def _clean_station_label(raw_label: str) -> str:
    """Strip HTML tags, leading '@' symbol, and excess whitespace."""
    cleaned = RE_HTML_TAGS.sub("", raw_label)
    cleaned = cleaned.strip()
    if cleaned.startswith("@"):
        cleaned = cleaned[1:].strip()
    return cleaned


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class BonAppetitParser(BaseParser):
    """Parser for Bon Appetit (BAMCO) dining halls.

    Supports Collins (CMC), Malott (Scripps), and McConnell (Pitzer).
    Extracts Bamco.menu_items and Bamco.dayparts from inline JavaScript
    via regex, filters by the ``special`` field, normalizes dietary tags
    from ``cor_icon``, and applies station filtering rules.
    """

    def __init__(self, hall_id: str, hall_name: str) -> None:
        if hall_id not in BAMCO_HALLS:
            raise ValueError(
                f"Unknown BAMCO hall: {hall_id!r}. "
                f"Must be one of {list(BAMCO_HALLS)}"
            )
        super().__init__(hall_id, hall_name)
        self._url_template = BAMCO_HALLS[hall_id]["url"]

    def build_url(self, target_date: date) -> str:
        """Format the cafe URL for the given date."""
        return self._url_template.format(date=target_date.isoformat())

    async def fetch_raw(self, target_date: date) -> str:
        """Fetch the raw HTML page from the BAMCO cafe site."""
        url = self.build_url(target_date)
        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, connect=10.0),
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def parse(self, raw_content: str, target_date: date) -> ParsedMenu:
        """Parse BAMCO page HTML into structured menu data.

        Steps:
        1. Extract Bamco.menu_items JSON object via regex
        2. Extract all Bamco.dayparts assignments via regex
        3. Build meals from dayparts, filtering by special field
        4. Apply station filtering pipeline
        """
        menu_items = self._extract_menu_items(raw_content)
        dayparts = self._extract_dayparts(raw_content)

        meals: list[ParsedMeal] = []
        for _dp_id, dp_data in dayparts.items():
            meal_label = dp_data.get("label", "Unknown")
            stations = self._build_stations(dp_data, menu_items)

            # Apply station filtering pipeline
            filtered = apply_station_filters(stations, BONAPPETIT_FILTER)

            if filtered:
                meals.append(ParsedMeal(meal=meal_label.lower(), stations=filtered))

        return ParsedMenu(hall_id=self.hall_id, date=target_date, meals=meals)

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_menu_items(html: str) -> dict:
        """Extract Bamco.menu_items JSON object from page HTML."""
        match = RE_MENU_ITEMS.search(html)
        if not match:
            raise ValueError("Could not find Bamco.menu_items in page")
        return json.loads(match.group(1))

    @staticmethod
    def _extract_dayparts(html: str) -> dict:
        """Extract all Bamco.dayparts assignments from page HTML."""
        dayparts: dict[str, dict] = {}
        for match in RE_DAYPARTS.finditer(html):
            dp_id = match.group(1)
            dp_data = json.loads(match.group(2))
            dayparts[dp_id] = dp_data

        if not dayparts:
            raise ValueError("Could not find Bamco.dayparts in page")
        return dayparts

    @staticmethod
    def _build_stations(
        daypart: dict,
        menu_items: dict,
    ) -> list[ParsedStation]:
        """Build ParsedStation list from a single daypart.

        Filters items by the ``special`` field (only truthy items included),
        extracts dietary tags from ``cor_icon``, cleans station labels,
        and deduplicates items within each station.
        """
        stations: list[ParsedStation] = []
        for station_data in daypart.get("stations", []):
            raw_label = station_data.get("label", "")
            station_name = _clean_station_label(raw_label)
            if not station_name:
                continue

            seen_labels: set[str] = set()
            items: list[ParsedMenuItem] = []
            for item_id in station_data.get("items", []):
                item_id_str = str(item_id)
                item_data = menu_items.get(item_id_str)
                if item_data is None:
                    continue

                # Filter by special field -- only include items being served
                if not item_data.get("special"):
                    continue

                label = item_data.get("label", "").strip()
                if not label:
                    continue

                # Deduplicate items within station (same label = keep first)
                label_lower = label.lower()
                if label_lower in seen_labels:
                    continue
                seen_labels.add(label_lower)

                # Extract dietary tags from cor_icon dict values
                cor_icon = item_data.get("cor_icon", {})
                raw_tags: list[str] = []
                if isinstance(cor_icon, dict):
                    raw_tags = list(cor_icon.values())
                tags = normalize_dietary_tags(raw_tags)

                items.append(ParsedMenuItem(name=label, tags=tags))

            stations.append(ParsedStation(name=station_name, items=items))

        return stations
