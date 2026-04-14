from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _normalize_url(database_url: str) -> str:
    """Ensure the URL uses an async-compatible driver.

    Cloud providers typically set DATABASE_URL with ``postgresql://`` or
    ``postgresql+psycopg2://``, but ``create_async_engine`` requires an
    async driver such as ``asyncpg``.
    """
    if database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(_normalize_url(database_url), pool_size=5, max_overflow=10)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
