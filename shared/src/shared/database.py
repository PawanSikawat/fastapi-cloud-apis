from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# libpq sslmode values that mean "use SSL"
_SSL_MODES = frozenset({"require", "verify-ca", "verify-full", "prefer", "allow"})


class Base(DeclarativeBase):
    pass


def _normalize_url(database_url: str) -> tuple[str, dict[str, Any]]:
    """Convert a libpq-style DATABASE_URL into an asyncpg-compatible one.

    Cloud providers (including FastAPI Cloud) set DATABASE_URL with the
    ``postgresql://`` scheme and libpq query parameters like ``sslmode``
    and ``channel_binding``.  asyncpg does not accept these — it uses its
    own keyword arguments (e.g. ``ssl``).

    This function:
    1. Rewrites the scheme to ``postgresql+asyncpg://``
    2. Strips **all** query parameters (they are libpq-specific)
    3. Returns ``connect_args`` with ``ssl=True`` when the original URL
       requested an SSL mode

    Returns:
        A ``(url, connect_args)`` tuple ready for ``create_async_engine``.
    """
    if database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(database_url)
    params = parse_qs(parsed.query)

    # Determine SSL requirement from the original sslmode param
    connect_args: dict[str, Any] = {}
    sslmode_values = params.get("sslmode", [])
    if sslmode_values and sslmode_values[0] in _SSL_MODES:
        connect_args["ssl"] = True

    # Strip all query params — they are libpq-specific and will cause
    # TypeError in asyncpg (sslmode, channel_binding, etc.)
    clean_url = urlunparse(parsed._replace(query=""))

    return clean_url, connect_args


def create_engine(database_url: str) -> AsyncEngine:
    url, connect_args = _normalize_url(database_url)
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
