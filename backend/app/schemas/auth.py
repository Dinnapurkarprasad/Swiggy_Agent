"""Request/response models for sign-in endpoints."""

import uuid

from pydantic import BaseModel, Field


class GoogleLogin(BaseModel):
    # The ID token Google's sign-in button hands to the frontend (it calls it "credential").
    credential: str = Field(min_length=1, max_length=4096)


class UserOut(BaseModel):
    """What the frontend may know about the logged-in host. Never includes google_sub."""

    id: uuid.UUID
    email: str
    name: str | None
