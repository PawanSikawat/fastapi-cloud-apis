from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from shared.auth.key_utils import generate_api_key
from shared.auth.models import ApiKey, User
from shared.database import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set env vars required by SharedSettings."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("COOKIE_SECRET_KEY", "test-cookie-secret")


@pytest.fixture
async def app():
    """Create app with test doubles for DB and Redis."""
    from email_validation.config import get_settings

    get_settings.cache_clear()

    from email_validation.main import create_app

    application = create_app()

    # Set up test doubles on app.state (lifespan does NOT run with ASGITransport)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    application.state.db_engine = engine
    application.state.db_session_factory = session_factory
    application.state.redis = fake_redis
    application.state.shared_settings = get_settings()

    # Seed a test API key
    async with session_factory() as session:
        user = User(email="test@test.com")
        session.add(user)
        await session.flush()

        full_key, prefix, key_hash = generate_api_key()
        api_key = ApiKey(key_prefix=prefix, key_hash=key_hash, user_id=user.id, plan="basic")
        session.add(api_key)
        await session.commit()

    application.state._test_api_key = full_key
    yield application

    await fake_redis.aclose()
    await engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient]:
    """HTTP client that automatically includes the test API key header."""
    api_key = app.state._test_api_key
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": api_key},
    ) as ac:
        yield ac
