"""Table models. Importing this package registers every table on SQLModel.metadata
(Alembic's env.py relies on that)."""

from app.models.guest import GuestResponse
from app.models.party import Party

__all__ = ["GuestResponse", "Party"]
