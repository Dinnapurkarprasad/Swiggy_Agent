"""summarize(): pure totals over guest responses."""

import uuid

from app.models import GuestResponse
from app.models.enums import Allergy, Cuisine, FoodType, HungerLevel
from app.planner.summary import summarize


def guest(**fields) -> GuestResponse:
    base = {"party_id": uuid.uuid4(), "name": "g", "food_type": "pure_veg", "spice": "mild"}
    # Mimic rows read from Postgres: arrays/enums arrive as plain strings.
    return GuestResponse(**{**base, **fields})


def test_empty_party() -> None:
    s = summarize([])
    assert s.responses == 0
    assert s.headcount == 0
    assert s.top_cuisines == []


def test_totals() -> None:
    s = summarize(
        [
            guest(food_type="jain", plus_ones=2, kids=True, cuisines=["south_indian"]),
            guest(
                food_type="non_veg",
                allergies=["nuts", "dairy"],
                cuisines=["biryani_mughlai", "south_indian"],
                hunger="very_hungry",
                dessert=True,
            ),
            guest(allergies=["nuts"], other_allergy="kiwi", beverage="none"),
        ]
    )
    assert s.responses == 3
    assert s.headcount == 5  # 3 guests + 2 plus-ones
    assert s.with_kids == 1
    assert s.food_types == {FoodType.JAIN: 1, FoodType.NON_VEG: 1, FoodType.PURE_VEG: 1}
    assert s.allergies == {Allergy.NUTS: 2, Allergy.DAIRY: 1}
    assert s.other_allergies == ["kiwi"]
    assert s.top_cuisines[0] == (Cuisine.SOUTH_INDIAN, 2)
    assert s.hunger == {HungerLevel.REGULAR: 2, HungerLevel.VERY_HUNGRY: 1}  # unanswered = regular
    assert s.beverages == {}  # "none" is not a drink
    assert s.want_dessert == 1
