"""Shared enums.

Diet / allergen / restriction values are mirrored in the frontend zod schema.
Change them here first, then regenerate/update the frontend so the two never drift.
"""

from enum import StrEnum


class FoodType(StrEnum):
    PURE_VEG = "pure_veg"  # no egg
    EGGETARIAN = "eggetarian"
    JAIN = "jain"  # no onion / garlic / root veg
    VEGAN = "vegan"
    NON_VEG = "non_veg"


class Restriction(StrEnum):
    """Only meaningful for NON_VEG guests."""

    HALAL_ONLY = "halal_only"
    NO_BEEF = "no_beef"
    NO_PORK = "no_pork"
    NO_SEAFOOD = "no_seafood"


class Allergy(StrEnum):
    NUTS = "nuts"
    DAIRY = "dairy"  # dairy / lactose
    GLUTEN = "gluten"
    SEAFOOD_SHELLFISH = "seafood_shellfish"


class SpiceLevel(StrEnum):
    MILD = "mild"
    MEDIUM = "medium"
    SPICY = "spicy"
    ANY = "any"  # doesn't matter


class Cuisine(StrEnum):
    NORTH_INDIAN = "north_indian"
    SOUTH_INDIAN = "south_indian"
    BIRYANI_MUGHLAI = "biryani_mughlai"
    TANDOOR_KEBABS = "tandoor_kebabs"
    STREET_FOOD_CHAAT = "street_food_chaat"
    THALI = "thali"
    CHINESE = "chinese"  # Chinese / Indo-Chinese
    THAI = "thai"
    JAPANESE = "japanese"
    PIZZA_ITALIAN = "pizza_italian"
    BURGERS_FAST_FOOD = "burgers_fast_food"
    CONTINENTAL = "continental"
    MEXICAN = "mexican"
    MIDDLE_EASTERN = "middle_eastern"
    HEALTHY_SALADS = "healthy_salads"
    ANYTHING = "anything"


class Beverage(StrEnum):
    SOFT_DRINK = "soft_drink"
    JUICE = "juice"
    LASSI_BUTTERMILK = "lassi_buttermilk"
    SHAKE_COLD_COFFEE = "shake_cold_coffee"
    MOCKTAIL = "mocktail"
    NONE = "none"


class HungerLevel(StrEnum):
    LIGHT = "light"
    REGULAR = "regular"
    VERY_HUNGRY = "very_hungry"


class PartyStatus(StrEnum):
    COLLECTING = "collecting"  # guest link open, responses coming in
    PLANNING = "planning"  # agent is building plans
    AWAITING_APPROVAL = "awaiting_approval"  # plans ready, host must choose
    ORDERING = "ordering"  # placing Swiggy orders
    DONE = "done"  # all orders placed / delivered
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    COD = "cod"
    UPI = "upi"


class SwiggyMode(StrEnum):
    MOCK = "mock"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(StrEnum):
    GEMINI = "gemini"
