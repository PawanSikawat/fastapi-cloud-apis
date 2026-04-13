from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

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
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("APP_REDIS_URL", "redis://localhost")
    monkeypatch.setenv("APP_COOKIE_SECRET_KEY", "test-cookie-secret")


@pytest.fixture
def mock_browser_pool() -> MagicMock:
    """A mock BrowserPool whose acquire() yields a mock Page returning fake PDF bytes."""
    pool = MagicMock()
    mock_page = AsyncMock()
    mock_page.pdf = AsyncMock(return_value=b"%PDF-1.4 fake pdf content")
    mock_page.set_content = AsyncMock()
    mock_page.goto = AsyncMock()

    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_page)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acquire_cm
    pool._mock_page = mock_page  # noqa: SLF001

    return pool


@pytest.fixture
async def app(mock_browser_pool: MagicMock):  # type: ignore[no-untyped-def]
    """Create app with test doubles for DB, Redis, and browser pool."""
    from pdf_from_html.config import get_settings

    get_settings.cache_clear()

    from pdf_from_html.main import create_app

    application = create_app()

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    application.state.db_engine = engine
    application.state.db_session_factory = session_factory
    application.state.redis = fake_redis
    application.state.shared_settings = get_settings()
    application.state.browser_pool = mock_browser_pool

    async with session_factory() as session:
        user = User(email="test@test.com")
        session.add(user)
        await session.flush()

        full_key, prefix, key_hash = generate_api_key()
        api_key = ApiKey(key_prefix=prefix, key_hash=key_hash, user_id=user.id, plan="basic")
        session.add(api_key)
        await session.commit()

    application.state._test_api_key = full_key  # noqa: SLF001
    yield application

    await fake_redis.aclose()
    await engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[no-untyped-def]
    """HTTP client that automatically includes the test API key header."""
    api_key = app.state._test_api_key  # noqa: SLF001
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": api_key},
    ) as ac:
        yield ac
