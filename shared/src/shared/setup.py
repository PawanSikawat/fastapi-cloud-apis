from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.config import SharedSettings
from shared.database import create_engine, create_session_factory
from shared.redis_client import create_redis


@asynccontextmanager
async def setup_shared(app: FastAPI, settings: SharedSettings) -> AsyncIterator[None]:
    """Initialize shared infrastructure. Use inside a project's lifespan."""
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    redis = create_redis(settings.redis_url)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.redis = redis
    app.state.shared_settings = settings

    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()
