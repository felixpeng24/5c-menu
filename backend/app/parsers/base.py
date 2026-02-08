import logging
from abc import ABC, abstractmethod
from datetime import date

import httpx

from app.models.menu import ParsedMenu

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for all dining hall parsers.

    Enforces fetch/parse separation: ``fetch_raw`` handles I/O,
    ``parse`` is a pure function testable against fixture files.
    """

    def __init__(self, hall_id: str, hall_name: str) -> None:
        self.hall_id = hall_id
        self.hall_name = hall_name

    @abstractmethod
    async def fetch_raw(self, target_date: date) -> str:
        """Fetch raw HTML/JSON from the vendor site.

        Returns the raw response text. All network I/O lives here.
        """

    @abstractmethod
    def parse(self, raw_content: str, target_date: date) -> ParsedMenu:
        """Parse raw content into structured menu data.

        Pure parsing logic -- no I/O. Testable against saved fixture files.
        """

    def validate(self, menu: ParsedMenu) -> bool:
        """Structural validation of a parsed menu.

        Returns True if the menu has at least one meal and each meal
        has at least ``min_station_count`` stations.
        """
        if not menu.meals:
            logger.warning("Validation failed for %s: no meals", self.hall_id)
            return False
        for meal in menu.meals:
            if len(meal.stations) < self.min_station_count:
                logger.warning(
                    "Validation failed for %s/%s: %d stations < %d minimum",
                    self.hall_id,
                    meal.meal,
                    len(meal.stations),
                    self.min_station_count,
                )
                return False
        return True

    @property
    def min_station_count(self) -> int:
        """Minimum stations required for a valid meal. Override per vendor."""
        return 1

    async def fetch_and_parse(self, target_date: date) -> ParsedMenu | None:
        """Full pipeline: fetch -> parse -> validate.

        Returns None if fetch fails or validation fails.
        """
        try:
            raw = await self.fetch_raw(target_date)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP %d fetching %s for %s",
                exc.response.status_code,
                self.hall_id,
                target_date,
            )
            return None
        except httpx.TimeoutException:
            logger.warning("Timeout fetching %s for %s", self.hall_id, target_date)
            return None
        except httpx.RequestError as exc:
            logger.warning(
                "Request error fetching %s for %s: %s",
                self.hall_id,
                target_date,
                exc,
            )
            return None

        try:
            menu = self.parse(raw, target_date)
        except Exception:
            logger.exception("Parse error for %s on %s", self.hall_id, target_date)
            return None

        if not self.validate(menu):
            return None

        return menu
