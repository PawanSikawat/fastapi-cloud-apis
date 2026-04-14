from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# asyncpg uses ``ssl`` instead of ``sslmode``.  Map common libpq values to the
# boolean that asyncpg expects so the connection just works regardless of what
# the cloud provider puts in DATABASE_URL.
_SSLMODE_TO_SSL: dict[str, bool] = {
    "require": True,
    "verify-ca": True,
    "verify-full": True,
    "prefer": True,
    "allow": True,
    "disable": False,
}


class Base(DeclarativeBase):
    pass


def _normalize_url(database_url: str) -> str:
    """Ensure the URL uses an async-compatible driver and query params.

    Cloud providers typically set DATABASE_URL with ``postgresql://`` or
    ``postgresql+psycopg2://``, but ``create_async_engine`` requires an
    async driver such as ``asyncpg``.

    They also commonly append ``?sslmode=require``, which asyncpg does not
    accept — it uses ``ssl`` instead.  This function converts the scheme
    **and** the query parameters so the URL is fully asyncpg-compatible.
    """
    if database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(database_url)
    params = parse_qs(parsed.query)

    if "sslmode" in params:
        sslmode = params.pop("sslmode")[0]
        ssl_value = _SSLMODE_TO_SSL.get(sslmode, True)
        if ssl_value:
            params["ssl"] = ["require"]
        new_query = urlencode(params, doseq=True)
        database_url = urlunparse(parsed._replace(query=new_query))

    return database_url


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(_normalize_url(database_url), pool_size=5, max_overflow=10)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
