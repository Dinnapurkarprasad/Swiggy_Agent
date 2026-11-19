"""Small helpers shared by all table models."""

from datetime import UTC, datetime
from enum import StrEnum

import sqlalchemy as sa


def utcnow() -> datetime:
    """Timezone-aware 'now'. Always store UTC; convert to IST only in the UI."""
    return datetime.now(UTC)


def enum_column(enum_cls: type[StrEnum]) -> sa.Enum:
    """Store a StrEnum as plain VARCHAR holding its *value* (e.g. 'pure_veg').

    native_enum=False avoids Postgres ENUM types, which are painful to change in migrations.
    values_callable makes SQLAlchemy store 'pure_veg' instead of the member name 'PURE_VEG'.
    """
    return sa.Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=30,
        values_callable=lambda e: [member.value for member in e],
    )
