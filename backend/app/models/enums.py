import enum


class MealPeriod(enum.Enum):
    BREAKFAST = "breakfast"
    BRUNCH = "brunch"
    LUNCH = "lunch"
    DINNER = "dinner"
    LATE_NIGHT = "late_night"


class College(enum.Enum):
    HMC = "hmc"
    CMC = "cmc"
    SCRIPPS = "scripps"
    PITZER = "pitzer"
    POMONA = "pomona"


class VendorType(enum.Enum):
    SODEXO = "sodexo"
    BONAPPETIT = "bonappetit"
    POMONA = "pomona"


class DietaryTag(enum.Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    GLUTEN_FREE = "gluten-free"
    HALAL = "halal"
    MINDFUL = "mindful"
    BALANCED = "balanced"
    FARM_TO_FORK = "farm-to-fork"
    HUMANE = "humane"
