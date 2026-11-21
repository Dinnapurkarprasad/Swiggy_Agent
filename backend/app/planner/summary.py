"""Party summary: turn guest responses into totals.

Pure function (no DB, no network) so it's easy to test. Used by the host dashboard now and
by the agent's aggregate_responses node later.
"""

from collections import Counter
from collections.abc import Sequence

from app.models import GuestResponse
from app.models.enums import (
    Allergy,
    Beverage,
    Cuisine,
    FoodType,
    HungerLevel,
    Restriction,
    SpiceLevel,
)
from app.schemas.party import PartySummary

TOP_CUISINES = 5


def summarize(responses: Sequence[GuestResponse]) -> PartySummary:
    food_types: Counter[FoodType] = Counter()
    restrictions: Counter[Restriction] = Counter()
    allergies: Counter[Allergy] = Counter()
    spice: Counter[SpiceLevel] = Counter()
    cuisines: Counter[Cuisine] = Counter()
    hunger: Counter[HungerLevel] = Counter()
    beverages: Counter[Beverage] = Counter()
    other_allergies: list[str] = []

    for r in responses:
        # Postgres arrays come back as plain strings, so convert them to enums here.
        food_types[FoodType(r.food_type)] += 1
        spice[SpiceLevel(r.spice)] += 1
        restrictions.update(Restriction(x) for x in r.restrictions)
        allergies.update(Allergy(x) for x in r.allergies)
        cuisines.update(Cuisine(x) for x in r.cuisines)
        hunger[HungerLevel(r.hunger) if r.hunger else HungerLevel.REGULAR] += 1
        if r.beverage and r.beverage != Beverage.NONE:
            beverages[Beverage(r.beverage)] += 1
        if r.other_allergy:
            other_allergies.append(r.other_allergy)

    return PartySummary(
        responses=len(responses),
        headcount=sum(1 + r.plus_ones for r in responses),
        with_kids=sum(1 for r in responses if r.kids),
        food_types=dict(food_types),
        restrictions=dict(restrictions),
        allergies=dict(allergies),
        other_allergies=other_allergies,
        spice=dict(spice),
        top_cuisines=cuisines.most_common(TOP_CUISINES),
        hunger=dict(hunger),
        beverages=dict(beverages),
        want_dessert=sum(1 for r in responses if r.dessert),
    )
