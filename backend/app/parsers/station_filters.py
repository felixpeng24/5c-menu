"""Station filtering pipeline and dietary tag normalization.

Replicates the v1 PHP station filtering logic exactly:
merge -> hide -> truncate -> sort -> remove empty.
"""

import logging
from dataclasses import dataclass, field

from app.models.menu import ParsedMenuItem, ParsedStation

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Station filter config
# ---------------------------------------------------------------------------


@dataclass
class StationFilterConfig:
    """Data-driven station filter configuration for a vendor."""

    hidden: list[str] = field(default_factory=list)
    ordered: list[str] = field(default_factory=list)
    truncated: dict[str, int] = field(default_factory=dict)
    combined: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Station filter pipeline
# ---------------------------------------------------------------------------


def _build_alias_map(combined: dict[str, list[str]]) -> dict[str, str]:
    """Build a reverse map: lowercase alias -> canonical display name."""
    alias_map: dict[str, str] = {}
    for canonical, aliases in combined.items():
        for alias in aliases:
            alias_map[alias.lower()] = canonical
    return alias_map


def apply_station_filters(
    stations: list[ParsedStation],
    config: StationFilterConfig,
) -> list[ParsedStation]:
    """Apply the full station filter pipeline matching v1 PHP logic.

    Pipeline order:
    1. Merge -- combine aliased stations under canonical names
    2. Hide -- remove hidden stations and those with truncated=-1
    3. Truncate -- limit item count for truncated stations
    4. Sort -- order by priority list
    5. Remove empty -- drop stations with zero items
    """

    # 1. MERGE: combine aliased stations
    alias_map = _build_alias_map(config.combined)
    merged: dict[str, ParsedStation] = {}
    merge_order: list[str] = []

    for station in stations:
        lower_name = station.name.lower()
        canonical = alias_map.get(lower_name, station.name)
        canonical_key = canonical.lower()

        if canonical_key in merged:
            # Append items to existing canonical station
            existing = merged[canonical_key]
            merged[canonical_key] = ParsedStation(
                name=existing.name,
                items=existing.items + station.items,
            )
        else:
            merged[canonical_key] = ParsedStation(
                name=canonical,
                items=list(station.items),
            )
            merge_order.append(canonical_key)

    merged_stations = [merged[k] for k in merge_order]

    # 2. HIDE: remove hidden stations and those with truncated=-1
    hidden_set = set(config.hidden)
    truncate_hidden = {k.lower() for k, v in config.truncated.items() if v == -1}
    visible = [
        s
        for s in merged_stations
        if s.name.lower() not in hidden_set and s.name.lower() not in truncate_hidden
    ]

    # 3. TRUNCATE: limit item counts for stations with positive truncation
    truncated: list[ParsedStation] = []
    for station in visible:
        lower_name = station.name.lower()
        limit = config.truncated.get(lower_name)
        if limit is not None and limit > 0:
            truncated.append(
                ParsedStation(name=station.name, items=station.items[:limit])
            )
        else:
            truncated.append(station)

    # 4. SORT: by position in ordered list; unlisted stations sort to end
    order_map = {name.lower(): idx for idx, name in enumerate(config.ordered)}

    def sort_key(station: ParsedStation) -> tuple[int, int]:
        idx = order_map.get(station.name.lower(), 999)
        # Preserve relative order of stations not in the list
        original_idx = next(
            (i for i, s in enumerate(truncated) if s is station), 999
        )
        return (idx, original_idx)

    sorted_stations = sorted(truncated, key=sort_key)

    # 5. REMOVE EMPTY: drop stations with 0 items
    return [s for s in sorted_stations if s.items]


# ---------------------------------------------------------------------------
# Vendor filter configs (matching v1 PHP exactly)
# ---------------------------------------------------------------------------

SODEXO_FILTER = StationFilterConfig(
    hidden=[
        "salad bar",
        "deli bar",
        "hot cereal",
        "sub connection",
        "deli bar hmc",
        "deli",
        "have a great day",
        "have a great day!",
        "rice",
        "potatoes",
        "sauces",
        "action-made to order",
    ],
    ordered=[
        "exhibition",
        "entree",
        "entrees",
        "dim sum",
        "entrees",
        "entree",
        "chicken entree",
        "beef entree",
        "fish/seafood entree",
        "pork",
        "action",
        "creations",
        "creations lto's",
        "breakfast grill",
        "chef's corner lto's",
        "chef's corner",
        "international",
        "oven",
        "taco bar",
        "breakfast",
        "grill breakfast",
        "grill",
        "the grill dinner",
        "vegetarian entrees",
        "special salad station",
        "veggie valley",
        "pasta/noodles",
        "pizza",
        "simple servings",
        "vegetables",
        "miscellaneous",
        "soups",
        "soup bar",
        "specialty salads",
        "hmc special salad",
        "salad",
        "hmc salad",
        "stg",
        "dessert",
        "desserts",
        "fruit bar",
        "bakery",
        "salad bar yogurt",
    ],
    truncated={
        "breakfast grill": 5,
        "salad bar": -1,
        "grill": 3,
        "omelet bar": -1,
        "breakfast": 12,
        "breakfast @home": 3,
        "breakfast options": -1,
        "international": 6,
        "burger shack": -1,
    },
    combined={
        "Special Salad Station": [
            "hmc salad",
            "special hot station salad north",
            "special bar salad-s",
            "special hot station salad south",
            "special station salad north",
            "special station salad south",
        ],
        "Miscellaneous": ["misc", "-"],
        "Soups": ["stew", "stews", "soup"],
        "Breakfast Grill": ["breakfast grill", "grill breakfast"],
        "The Grill Dinner": ["the grill dinner"],
        "Entree": ["entree", "entrees", "entree", "entrees"],
    },
)

BONAPPETIT_FILTER = StationFilterConfig(
    hidden=[
        "breakfast toppings",
        "breads, bagels and spreads",
        "cold cereals",
        "cold cereal",
        "fruits and yogurts",
        "beverage",
        "beverages",
        "build your own sandwich",
        "cereal",
        "toppings & condiments",
        "deli bar",
    ],
    ordered=[
        "chef's table",
        "main plate",
        "breakfast",
        "breakfast @home",
        "@home",
        "@ home",
        "breakfast options",
        "expo",
        "global",
        "options",
        "expo - mongolian",
        "expo - little italy",
        "grill",
        "pasta - express",
        "ovens",
        "collins late night snack",
        "ovens",
        "vegan",
        "vegan salads",
        "vegan - hummus & pita",
        "sweets",
        "stock pot",
        "stocks",
    ],
    truncated={
        "breakfast grill": 5,
        "salad bar": -1,
        "grill": 3,
        "omelet bar": -1,
        "breakfast": 12,
        "breakfast @home": 3,
        "breakfast options": 5,
        "juice and smoothie bar": -1,
        "expo - mongolian": -1,
        "expo - little italy": 3,
        "chef's table - pasta bar": -1,
        "chef's table - taco bar": -1,
    },
    combined={
        "grill special": ["grill"],
        "sweets": ["sweets", "chocolate chip cookies"],
        "main plate": ["main plate", "main plate in balance"],
        "ovens": ["ovens", "ovens2"],
    },
)

POMONA_FILTER = StationFilterConfig(
    hidden=[],
    ordered=[
        "entree",
        "expo",
        "grill",
        "mainline",
        "starch",
        "pizza",
        "allergen friendly station",
        "salad",
        "salad bar",
        "vegetable",
        "vegan/veggie",
        "soup",
        "deli-salad",
        "dessert",
    ],
    truncated={
        "breakfast grill": 5,
    },
    combined={
        "Grill": ["grill", "grill station"],
        "Soup": ["soup", "soup station", "soups"],
        "Expo": ["expo", "expo station"],
    },
)


# ---------------------------------------------------------------------------
# Dietary tag normalization
# ---------------------------------------------------------------------------

DIETARY_TAG_MAP: dict[str, str] = {
    # Sodexo boolean fields
    "isvegan": "vegan",
    "isvegetarian": "vegetarian",
    "ismindful": "mindful",
    # Bon Appetit cor_icon values
    "vegan": "vegan",
    "vegetarian": "vegetarian",
    "made without gluten-containing ingredients": "gluten-free",
    "in balance": "balanced",
    "farm to fork": "farm-to-fork",
    "humane": "humane",
    "halal": "halal",
    # Pomona dietaryChoices
    # "vegetarian" and "vegan" already mapped above
    "gluten free": "gluten-free",
}


def normalize_dietary_tags(raw_tags: list[str]) -> list[str]:
    """Normalize vendor-specific dietary labels to canonical tag strings.

    Unknown tags are dropped with a log warning. Returns a sorted,
    deduplicated list of canonical tags.
    """
    canonical: set[str] = set()
    for tag in raw_tags:
        mapped = DIETARY_TAG_MAP.get(tag.lower())
        if mapped is not None:
            canonical.add(mapped)
        else:
            logger.warning("Unknown dietary tag dropped: %r", tag)
    return sorted(canonical)


# ---------------------------------------------------------------------------
# Sodexo station name normalization
# ---------------------------------------------------------------------------


def normalize_sodexo_station_name(raw_name: str) -> str:
    """Normalize a Sodexo station name matching v1 PHP behavior.

    - Strips trailing " SCR" suffix
    - Applies title case when name is ALL CAPS, then fixes common words
    - Returns "Miscellaneous" for blank/dash-only names
    """
    name = raw_name.strip()

    # Blank or dash-only -> Miscellaneous
    if not name or name == "-":
        return "Miscellaneous"

    # Strip trailing " SCR" suffix
    if name.endswith(" SCR"):
        name = name[:-4].rstrip()

    # If ALL CAPS, apply title case with fixes
    if name.isupper():
        name = name.title()
        # Fix common title-case artifacts
        name = name.replace(" And ", " and ")
        name = name.replace(" To ", " to ")
        name = name.replace("Hmc", "HMC")

    return name.strip()
