"""User: a host who signed in with Google. Guests are not users (they never log in)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.models.base import utcnow


class User(SQLModel, table=True):
    # "user" is a reserved word in Postgres, so the table is "app_user".
    __tablename__ = "app_user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Google's permanent id for this account (the "sub" claim). We look users up by this,
    # not by email, because a Google account's email can change.
    google_sub: str = Field(max_length=255, unique=True, index=True)

    email: str = Field(max_length=320)
    name: str | None = Field(default=None, max_length=100)

    created_at: datetime = Field(default_factory=utcnow, sa_type=sa.DateTime(timezone=True))
