from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import fakeredis.aioredis
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared.auth.key_utils import generate_api_key
from shared.auth.middleware import AuthMiddleware
from shared.auth.models import ApiKey, User
from shared.config import SharedSettings
from shared.database import Base
from shared.metering.middleware import MeteringMiddleware
from shared.middleware.channel_detect import ChannelDetectMiddleware
from shared.rate_limit.middleware import RateLimitMiddleware


@pytest.fixture
async def test_app():
    """Build a minimal FastAPI app with the full shared middleware stack."""
    app = FastAPI()

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.redis = redis
    app.state.shared_settings = MagicMock(spec=SharedSettings, rapidapi_proxy_secret="test-secret")

    app.add_middleware(MeteringMiddleware, api_name="test-api")
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ChannelDetectMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    async with session_factory() as session:
        user = User(email="integration@test.com")
        session.add(user)
        await session.flush()

        full_key, prefix, key_hash = generate_api_key()
        key = ApiKey(key_prefix=prefix, key_hash=key_hash, user_id=user.id, plan="basic")
        session.add(key)
        await session.commit()

    app.state._test_api_key = full_key
    yield app

    await redis.aclose()
    await engine.dispose()


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


class TestFullMiddlewareStack:
    @pytest.mark.asyncio
    async def test_health_bypasses_auth(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_key_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/test")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_key_succeeds(self, test_app: FastAPI, client: AsyncClient) -> None:
        key = test_app.state._test_api_key
        response = await client.get("/test", headers={"x-api-key": key})
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-Usage-Current" in response.headers

    @pytest.mark.asyncio
    async def test_invalid_key_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/test", headers={"x-api-key": "sk_bogus"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, test_app: FastAPI, client: AsyncClient) -> None:
        key = test_app.state._test_api_key
        response = await client.get("/test", headers={"x-api-key": key})
        assert response.headers["X-RateLimit-Limit"] == "60"

    @pytest.mark.asyncio
    async def test_rapidapi_channel(self, client: AsyncClient) -> None:
        response = await client.get(
            "/test",
            headers={
                "x-rapidapi-proxy-secret": "test-secret",
                "x-rapidapi-user": "testuser",
                "x-rapidapi-subscription": "PRO",
            },
        )
        assert response.status_code == 200
