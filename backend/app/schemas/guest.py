"""Request/response models for the guest form."""

import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.enums import (
    Allergy,
    Beverage,
    Cuisine,
    FoodType,
    HungerLevel,
    Restriction,
    SpiceLevel,
)

GuestName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
MAX_CUISINES = 3


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class GuestResponseCreate(BaseModel):
    """What a guest submits. Required: name, food_type, spice (PRD section 6)."""

    name: GuestName
    food_type: FoodType
    spice: SpiceLevel

    plus_ones: int = Field(default=0, ge=0, le=3)
    kids: bool = False
    restrictions: list[Restriction] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    other_allergy: str | None = Field(default=None, max_length=100)
    cuisines: list[Cuisine] = Field(default_factory=list)
    fav_dish: str | None = Field(default=None, max_length=60)
    beverage: Beverage | None = None
    hunger: HungerLevel | None = None
    dessert: bool | None = None

    @field_validator("restrictions", "allergies", "cuisines")
    @classmethod
    def drop_duplicates(cls, values: list) -> list:
        # ["nuts", "nuts"] -> ["nuts"], keeping the guest's order.
        return list(dict.fromkeys(values))

    @field_validator("other_allergy", "fav_dish")
    @classmethod
    def blank_is_none(cls, value: str | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def check_form_rules(self) -> Self:
        if self.restrictions and self.food_type != FoodType.NON_VEG:
            raise ValueError("restrictions only apply to non-veg guests")
        if len(self.cuisines) > MAX_CUISINES:
            raise ValueError(f"pick at most {MAX_CUISINES} cuisines")
        if Cuisine.ANYTHING in self.cuisines and len(self.cuisines) > 1:
            raise ValueError("'anything' can't be combined with other cuisines")
        return self


class GuestResponseCreated(BaseModel):
    """Confirmation shown to the guest after submitting."""

    id: uuid.UUID
    party_id: uuid.UUID
    name: str


class GuestResponseOut(BaseModel):
    """A full response, shown only to the party's host."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    food_type: FoodType
    spice: SpiceLevel
    plus_ones: int
    kids: bool
    restrictions: list[Restriction]
    allergies: list[Allergy]
    other_allergy: str | None
    cuisines: list[Cuisine]
    fav_dish: str | None
    beverage: Beverage | None
    hunger: HungerLevel | None
    dessert: bool | None
    created_at: datetime
