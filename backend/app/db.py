"""Async database engine and session dependency."""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    # Created lazily so the app (and tests) can start without a database.
    return create_async_engine(
        get_settings().database_url.get_secret_value(),
        pool_pre_ping=True,
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    async with get_sessionmaker()() as session:
        yield session


# Use in route signatures: `async def route(session: SessionDep)`.
SessionDep = Annotated[AsyncSession, Depends(get_session)]
