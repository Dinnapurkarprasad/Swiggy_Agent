"""GuestResponse: one row per guest form submission (many per party)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel

from app.models.base import enum_column, utcnow
from app.models.enums import (
    Allergy,
    Beverage,
    Cuisine,
    FoodType,
    HungerLevel,
    Restriction,
    SpiceLevel,
)


class GuestResponse(SQLModel, table=True):
    __tablename__ = "guest_response"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign key: which party this answer belongs to. Deleting a party deletes its responses.
    party_id: uuid.UUID = Field(foreign_key="party.id", index=True, ondelete="CASCADE")

    # --- Required answers ---
    name: str = Field(max_length=50)
    food_type: FoodType = Field(sa_type=enum_column(FoodType))
    spice: SpiceLevel = Field(sa_type=enum_column(SpiceLevel))

    # --- Optional answers ---
    plus_ones: int = Field(default=0, ge=0, le=3)
    kids: bool = Field(default=False)

    # Multi-selects are Postgres arrays, so we can query e.g. "who is allergic to nuts".
    restrictions: list[Restriction] = Field(default_factory=list, sa_type=ARRAY(sa.String(30)))
    allergies: list[Allergy] = Field(default_factory=list, sa_type=ARRAY(sa.String(30)))
    other_allergy: str | None = Field(default=None, max_length=100)  # free text from "Other"
    cuisines: list[Cuisine] = Field(default_factory=list, sa_type=ARRAY(sa.String(30)))

    fav_dish: str | None = Field(default=None, max_length=60)
    beverage: Beverage | None = Field(default=None, sa_type=enum_column(Beverage))
    hunger: HungerLevel | None = Field(default=None, sa_type=enum_column(HungerLevel))
    dessert: bool | None = Field(default=None)

    created_at: datetime = Field(default_factory=utcnow, sa_type=sa.DateTime(timezone=True))
