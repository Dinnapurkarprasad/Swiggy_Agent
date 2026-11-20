"""Party: one row per party a host creates."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.models.base import enum_column, utcnow
from app.models.enums import PartyStatus


class Party(SQLModel, table=True):
    __tablename__ = "party"

    # Public id. It appears in the guest link: /p/{id}
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    name: str = Field(max_length=100)
    party_at: datetime = Field(sa_type=sa.DateTime(timezone=True))

    # Swiggy saved-address id. Filled after the host connects Swiggy (OAuth, Milestone 5).
    address_id: str | None = Field(default=None, max_length=64)

    # Money is integer paise (₹1 = 100 paise), never float.
    budget_per_person_paise: int | None = Field(default=None, ge=0)

    rsvp_deadline: datetime | None = Field(default=None, sa_type=sa.DateTime(timezone=True))

    # The signed-in host who created this party. Deleting the user deletes their parties.
    host_user_id: uuid.UUID = Field(foreign_key="app_user.id", index=True, ondelete="CASCADE")

    status: PartyStatus = Field(default=PartyStatus.COLLECTING, sa_type=enum_column(PartyStatus))

    created_at: datetime = Field(default_factory=utcnow, sa_type=sa.DateTime(timezone=True))
