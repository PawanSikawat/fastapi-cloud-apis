import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.auth.key_utils import hash_api_key
from shared.auth.models import ApiKey, User
from shared.config import SharedSettings
from shared.database import Base, create_engine, create_session_factory
from shared.redis_client import create_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def setup_shared(app: FastAPI, settings: SharedSettings) -> AsyncIterator[None]:
    """Initialize shared infrastructure. Use inside a project's lifespan."""
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    redis = create_redis(settings.redis_url)

    # Create tables if they don't exist (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed admin user/key if ADMIN_API_KEY is configured
    if settings.admin_api_key:
        await _ensure_admin(session_factory, settings)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.redis = redis
    app.state.shared_settings = settings

    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()


async def _ensure_admin(
    session_factory: async_sessionmaker[AsyncSession],
    settings: SharedSettings,
) -> None:
    """Create admin user and register the API key if not already present."""
    key_hash = hash_api_key(settings.admin_api_key)

    async with session_factory() as session:
        # Check if this key already exists
        existing = await session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        if existing.scalar_one_or_none() is not None:
            return

        # Get or create admin user
        result = await session.execute(select(User).where(User.email == settings.admin_email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=settings.admin_email)
            session.add(user)
            await session.flush()

        # Register the admin API key
        prefix = settings.admin_api_key[:12]
        api_key = ApiKey(
            key_prefix=prefix,
            key_hash=key_hash,
            user_id=user.id,
            plan="admin",
        )
        session.add(api_key)
        await session.commit()
        logger.info("Admin API key registered for %s", settings.admin_email)
