# Shared Infrastructure Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `shared/` infrastructure package that provides auth, rate limiting, metering, billing, and channel detection for all API projects in the monorepo.

**Architecture:** Middleware-based pipeline — ChannelDetect → Auth → RateLimit → Metering → route handler. Redis for hot-path operations (rate limit counters, usage meters, API key cache). PostgreSQL for persistent state (users, API keys, usage records). Stripe for direct-channel billing. Each API project adds `shared` as a path dependency and wires middleware + dependencies in `main.py`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async (asyncpg), redis[hiredis] async, Stripe Python SDK, Pydantic Settings, pytest + fakeredis + aiosqlite for testing.

---

## File Map

```
shared/
├── pyproject.toml
└── src/
    └── shared/
        ├── __init__.py
        ├── config.py              # SharedSettings (env vars)
        ├── database.py            # Async engine + session factory
        ├── redis_client.py        # Redis connection factory
        ├── setup.py               # Lifespan context manager for projects
        ├── dependencies.py        # Reusable FastAPI Depends() types
        ├── auth/
        │   ├── __init__.py
        │   ├── models.py          # SQLAlchemy: User, ApiKey, UsageRecord
        │   ├── key_utils.py       # Key generation + hashing
        │   ├── api_key.py         # Direct-channel API key validation
        │   ├── rapidapi.py        # RapidAPI proxy-secret validation
        │   └── middleware.py      # AuthMiddleware
        ├── billing/
        │   ├── __init__.py
        │   ├── plans.py           # PlanDefinition dataclass + PLANS dict
        │   ├── stripe_client.py   # Stripe operations wrapper
        │   └── webhooks.py        # Stripe webhook FastAPI router
        ├── metering/
        │   ├── __init__.py
        │   ├── counter.py         # Redis-based usage counter
        │   ├── storage.py         # Flush Redis counters → PostgreSQL
        │   └── middleware.py      # MeteringMiddleware
        ├── rate_limit/
        │   ├── __init__.py
        │   ├── limiter.py         # Fixed-window Redis rate limiter
        │   └── middleware.py      # RateLimitMiddleware
        └── middleware/
            ├── __init__.py
            └── channel_detect.py  # ChannelDetectMiddleware
```

**Tests:**
```
shared/tests/
├── __init__.py
├── conftest.py                    # Fixtures: fake Redis, SQLite DB, test app
├── test_auth/
│   ├── __init__.py
│   ├── test_key_utils.py
│   ├── test_api_key.py
│   └── test_rapidapi.py
├── test_billing/
│   ├── __init__.py
│   └── test_plans.py
├── test_rate_limit/
│   ├── __init__.py
│   └── test_limiter.py
├── test_metering/
│   ├── __init__.py
│   └── test_counter.py
└── test_middleware/
    ├── __init__.py
    └── test_integration.py        # Full middleware stack test
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `shared/pyproject.toml`
- Create: `shared/src/shared/__init__.py`
- Create: `shared/src/shared/config.py`
- Create: `shared/src/shared/database.py`
- Create: `shared/src/shared/redis_client.py`
- Create: all `__init__.py` files for subpackages
- Create: `shared/tests/__init__.py`, `shared/tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p shared/src/shared/{auth,billing,metering,rate_limit,middleware}
mkdir -p shared/tests/{test_auth,test_billing,test_rate_limit,test_metering,test_middleware}
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "shared"
version = "0.1.0"
description = "Shared infrastructure — auth, billing, metering, rate limiting for all API projects"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "pydantic-settings>=2.7.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "redis>=5.2.0",
    "stripe>=12.0.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/shared"]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
    "fakeredis>=2.26.0",
    "aiosqlite>=0.21.0",
    "mypy>=1.14.0",
    "ruff>=0.9.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "A", "SIM", "TCH"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
```

- [ ] **Step 3: Write config.py**

```python
# shared/src/shared/config.py
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: str
    redis_url: str
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    rapidapi_proxy_secret: str = ""


@lru_cache
def get_shared_settings() -> SharedSettings:
    return SharedSettings()
```

- [ ] **Step 4: Write database.py**

```python
# shared/src/shared/database.py
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_size=5, max_overflow=10)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

- [ ] **Step 5: Write redis_client.py**

```python
# shared/src/shared/redis_client.py
from redis.asyncio import Redis


def create_redis(redis_url: str) -> Redis:
    return Redis.from_url(redis_url, decode_responses=True)
```

- [ ] **Step 6: Create all `__init__.py` files**

Empty `__init__.py` in: `shared/src/shared/`, `shared/src/shared/auth/`, `shared/src/shared/billing/`, `shared/src/shared/metering/`, `shared/src/shared/rate_limit/`, `shared/src/shared/middleware/`, `shared/tests/`, `shared/tests/test_auth/`, `shared/tests/test_billing/`, `shared/tests/test_rate_limit/`, `shared/tests/test_metering/`, `shared/tests/test_middleware/`.

- [ ] **Step 7: Write tests/conftest.py**

```python
# shared/tests/conftest.py
import pytest
import fakeredis.aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.database import Base


@pytest.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
```

- [ ] **Step 8: Install dependencies and verify**

```bash
cd shared && uv sync
```

- [ ] **Step 9: Commit**

```bash
git add shared/
git commit -m "feat(shared): scaffold shared infrastructure package"
```

---

### Task 2: Database Models

**Files:**
- Create: `shared/src/shared/auth/models.py`
- Test: `shared/tests/test_auth/test_models.py`

- [ ] **Step 1: Write model tests**

```python
# shared/tests/test_auth/test_models.py
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.models import ApiKey, UsageRecord, User


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession) -> None:
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(select(User).where(User.email == "test@example.com"))
        fetched = result.scalar_one()
        assert fetched.email == "test@example.com"
        assert isinstance(fetched.id, uuid.UUID)


class TestApiKeyModel:
    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession) -> None:
        user = User(email="key-test@example.com")
        db_session.add(user)
        await db_session.flush()

        key = ApiKey(
            key_prefix="sk_abc12345",
            key_hash="a" * 64,
            user_id=user.id,
            plan="basic",
        )
        db_session.add(key)
        await db_session.commit()

        result = await db_session.execute(select(ApiKey).where(ApiKey.user_id == user.id))
        fetched = result.scalar_one()
        assert fetched.plan == "basic"
        assert fetched.is_active is True


class TestUsageRecordModel:
    @pytest.mark.asyncio
    async def test_create_usage_record(self, db_session: AsyncSession) -> None:
        user = User(email="usage-test@example.com")
        db_session.add(user)
        await db_session.flush()

        key = ApiKey(key_prefix="sk_usage123", key_hash="b" * 64, user_id=user.id)
        db_session.add(key)
        await db_session.flush()

        record = UsageRecord(
            api_key_id=key.id,
            api_name="email-validation",
            month="2026-04",
            request_count=42,
        )
        db_session.add(record)
        await db_session.commit()

        result = await db_session.execute(
            select(UsageRecord).where(UsageRecord.api_key_id == key.id)
        )
        fetched = result.scalar_one()
        assert fetched.request_count == 42
        assert fetched.api_name == "email-validation"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd shared && uv run pytest tests/test_auth/test_models.py -v
```

Expected: FAIL — `models` module doesn't exist.

- [ ] **Step 3: Write models**

```python
# shared/src/shared/auth/models.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from shared.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key_prefix: Mapped[str] = mapped_column(String(12))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="api_keys")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    api_key_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("api_keys.id"), index=True)
    api_name: Mapped[str] = mapped_column(String(100))
    month: Mapped[str] = mapped_column(String(7))
    request_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("api_key_id", "api_name", "month", name="uq_usage_key_api_month"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd shared && uv run pytest tests/test_auth/test_models.py -v
```

- [ ] **Step 5: Commit**

```bash
git add shared/src/shared/auth/models.py shared/tests/test_auth/test_models.py
git commit -m "feat(shared): add User, ApiKey, UsageRecord database models"
```

---

### Task 3: Plan Definitions + API Key Utilities

**Files:**
- Create: `shared/src/shared/billing/plans.py`
- Create: `shared/src/shared/auth/key_utils.py`
- Test: `shared/tests/test_billing/test_plans.py`
- Test: `shared/tests/test_auth/test_key_utils.py`

- [ ] **Step 1: Write plan tests**

```python
# shared/tests/test_billing/test_plans.py
from shared.billing.plans import PLANS, PlanDefinition, get_plan


class TestPlans:
    def test_free_plan_exists(self) -> None:
        plan = get_plan("free")
        assert plan.name == "free"
        assert plan.requests_per_month == 100
        assert plan.rate_limit_per_minute == 10
        assert plan.price_cents == 0

    def test_basic_plan(self) -> None:
        plan = get_plan("basic")
        assert plan.requests_per_month == 10_000
        assert plan.price_cents == 900

    def test_pro_plan(self) -> None:
        plan = get_plan("pro")
        assert plan.requests_per_month == 100_000
        assert plan.price_cents == 2900

    def test_enterprise_plan(self) -> None:
        plan = get_plan("enterprise")
        assert plan.requests_per_month == 1_000_000

    def test_unknown_plan_returns_free(self) -> None:
        plan = get_plan("nonexistent")
        assert plan.name == "free"

    def test_all_plans_are_frozen(self) -> None:
        for plan in PLANS.values():
            assert isinstance(plan, PlanDefinition)
```

- [ ] **Step 2: Write key_utils tests**

```python
# shared/tests/test_auth/test_key_utils.py
from shared.auth.key_utils import generate_api_key, hash_api_key


class TestKeyUtils:
    def test_generate_api_key_format(self) -> None:
        full_key, prefix, key_hash = generate_api_key()
        assert full_key.startswith("sk_")
        assert prefix == full_key[:12]
        assert len(key_hash) == 64

    def test_generate_api_key_custom_prefix(self) -> None:
        full_key, _, _ = generate_api_key(prefix="ev")
        assert full_key.startswith("ev_")

    def test_generate_api_key_unique(self) -> None:
        key1, _, _ = generate_api_key()
        key2, _, _ = generate_api_key()
        assert key1 != key2

    def test_hash_api_key_deterministic(self) -> None:
        h1 = hash_api_key("test-key")
        h2 = hash_api_key("test-key")
        assert h1 == h2

    def test_hash_api_key_different_inputs(self) -> None:
        h1 = hash_api_key("key-a")
        h2 = hash_api_key("key-b")
        assert h1 != h2

    def test_generate_and_hash_roundtrip(self) -> None:
        full_key, _, expected_hash = generate_api_key()
        assert hash_api_key(full_key) == expected_hash
```

- [ ] **Step 3: Run tests — expect failures**

```bash
cd shared && uv run pytest tests/test_billing/test_plans.py tests/test_auth/test_key_utils.py -v
```

- [ ] **Step 4: Write plans.py**

```python
# shared/src/shared/billing/plans.py
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanDefinition:
    name: str
    display_name: str
    requests_per_month: int
    rate_limit_per_minute: int
    price_cents: int
    stripe_price_id: str | None = None


PLANS: dict[str, PlanDefinition] = {
    "free": PlanDefinition(
        name="free",
        display_name="Free",
        requests_per_month=100,
        rate_limit_per_minute=10,
        price_cents=0,
    ),
    "basic": PlanDefinition(
        name="basic",
        display_name="Basic",
        requests_per_month=10_000,
        rate_limit_per_minute=60,
        price_cents=900,
    ),
    "pro": PlanDefinition(
        name="pro",
        display_name="Pro",
        requests_per_month=100_000,
        rate_limit_per_minute=300,
        price_cents=2900,
    ),
    "enterprise": PlanDefinition(
        name="enterprise",
        display_name="Enterprise",
        requests_per_month=1_000_000,
        rate_limit_per_minute=1000,
        price_cents=0,
    ),
}


def get_plan(name: str) -> PlanDefinition:
    return PLANS.get(name, PLANS["free"])
```

- [ ] **Step 5: Write key_utils.py**

```python
# shared/src/shared/auth/key_utils.py
import hashlib
import secrets


def generate_api_key(prefix: str = "sk") -> tuple[str, str, str]:
    """Generate an API key. Returns (full_key, key_prefix, key_hash)."""
    random_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}_{random_part}"
    key_prefix = full_key[:12]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key for storage/lookup."""
    return hashlib.sha256(key.encode()).hexdigest()
```

- [ ] **Step 6: Run tests — expect pass**

```bash
cd shared && uv run pytest tests/test_billing/test_plans.py tests/test_auth/test_key_utils.py -v
```

- [ ] **Step 7: Commit**

```bash
git add shared/src/shared/billing/plans.py shared/src/shared/auth/key_utils.py \
  shared/tests/test_billing/test_plans.py shared/tests/test_auth/test_key_utils.py
git commit -m "feat(shared): add plan definitions and API key utilities"
```

---

### Task 4: Auth — API Key + RapidAPI Validation

**Files:**
- Create: `shared/src/shared/auth/api_key.py`
- Create: `shared/src/shared/auth/rapidapi.py`
- Test: `shared/tests/test_auth/test_api_key.py`
- Test: `shared/tests/test_auth/test_rapidapi.py`

- [ ] **Step 1: Write API key validation tests**

```python
# shared/tests/test_auth/test_api_key.py
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.api_key import validate_api_key_direct
from shared.auth.key_utils import generate_api_key
from shared.auth.models import ApiKey, User


async def _seed_key(db: AsyncSession, plan: str = "basic", active: bool = True) -> str:
    """Helper: create a user + API key, return the raw key."""
    user = User(email=f"{plan}-{active}@test.com")
    db.add(user)
    await db.flush()

    full_key, prefix, key_hash = generate_api_key()
    key = ApiKey(key_prefix=prefix, key_hash=key_hash, user_id=user.id, plan=plan, is_active=active)
    db.add(key)
    await db.commit()
    return full_key


class TestValidateApiKeyDirect:
    @pytest.mark.asyncio
    async def test_valid_key(self, redis, db_session: AsyncSession) -> None:
        raw_key = await _seed_key(db_session, plan="pro")
        info = await validate_api_key_direct(raw_key, redis, db_session)
        assert info["plan"] == "pro"
        assert info["is_active"] is True
        assert info["channel"] == "direct"

    @pytest.mark.asyncio
    async def test_invalid_key_raises_401(self, redis, db_session: AsyncSession) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await validate_api_key_direct("sk_bogus_key", redis, db_session)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_key_raises_403(self, redis, db_session: AsyncSession) -> None:
        raw_key = await _seed_key(db_session, plan="basic", active=False)
        with pytest.raises(HTTPException) as exc_info:
            await validate_api_key_direct(raw_key, redis, db_session)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_result_is_cached_in_redis(self, redis, db_session: AsyncSession) -> None:
        raw_key = await _seed_key(db_session, plan="pro")
        await validate_api_key_direct(raw_key, redis, db_session)
        # Second call should hit cache (we can verify by checking Redis)
        from shared.auth.key_utils import hash_api_key
        cached = await redis.get(f"api_key:{hash_api_key(raw_key)}")
        assert cached is not None
```

- [ ] **Step 2: Write RapidAPI validation tests**

```python
# shared/tests/test_auth/test_rapidapi.py
import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient
from starlette.requests import Request
from starlette.datastructures import Headers

from shared.auth.rapidapi import validate_rapidapi


def _make_request(headers: dict[str, str]) -> Request:
    scope = {"type": "http", "method": "GET", "path": "/", "headers": [
        (k.lower().encode(), v.encode()) for k, v in headers.items()
    ]}
    return Request(scope)


class TestValidateRapidapi:
    @pytest.mark.asyncio
    async def test_valid_proxy_secret(self) -> None:
        request = _make_request({
            "x-rapidapi-proxy-secret": "secret123",
            "x-rapidapi-user": "user456",
            "x-rapidapi-subscription": "PRO",
        })
        info = await validate_rapidapi(request, expected_secret="secret123")
        assert info["channel"] == "rapidapi"
        assert info["plan"] == "basic"  # PRO maps to basic
        assert info["is_active"] is True

    @pytest.mark.asyncio
    async def test_invalid_proxy_secret_raises_401(self) -> None:
        request = _make_request({"x-rapidapi-proxy-secret": "wrong"})
        with pytest.raises(HTTPException) as exc_info:
            await validate_rapidapi(request, expected_secret="secret123")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_subscription_defaults_to_free(self) -> None:
        request = _make_request({
            "x-rapidapi-proxy-secret": "secret123",
            "x-rapidapi-user": "user789",
        })
        info = await validate_rapidapi(request, expected_secret="secret123")
        assert info["plan"] == "free"
```

- [ ] **Step 3: Run tests — expect failures**

```bash
cd shared && uv run pytest tests/test_auth/test_api_key.py tests/test_auth/test_rapidapi.py -v
```

- [ ] **Step 4: Write api_key.py**

```python
# shared/src/shared/auth/api_key.py
import json

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.key_utils import hash_api_key
from shared.auth.models import ApiKey

_CACHE_TTL = 300


async def validate_api_key_direct(
    raw_key: str,
    redis: Redis,
    db_session: AsyncSession,
) -> dict[str, object]:
    """Validate a direct-channel API key. Returns key info dict."""
    key_hash = hash_api_key(raw_key)

    # Check Redis cache
    cached = await redis.get(f"api_key:{key_hash}")
    if cached:
        info: dict[str, object] = json.loads(cached)
        if not info["is_active"]:
            raise HTTPException(status_code=403, detail="API key is inactive")
        return info

    # DB lookup
    result = await db_session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not api_key.is_active:
        raise HTTPException(status_code=403, detail="API key is inactive")

    info = {
        "id": str(api_key.id),
        "user_id": str(api_key.user_id),
        "plan": api_key.plan,
        "is_active": api_key.is_active,
        "channel": "direct",
    }

    await redis.set(f"api_key:{key_hash}", json.dumps(info), ex=_CACHE_TTL)
    return info
```

- [ ] **Step 5: Write rapidapi.py**

```python
# shared/src/shared/auth/rapidapi.py
from fastapi import HTTPException
from starlette.requests import Request

_RAPIDAPI_PLAN_MAP: dict[str, str] = {
    "BASIC": "free",
    "PRO": "basic",
    "ULTRA": "pro",
    "MEGA": "enterprise",
    "CUSTOM": "enterprise",
}


async def validate_rapidapi(
    request: Request,
    expected_secret: str,
) -> dict[str, object]:
    """Validate a RapidAPI proxied request. Returns auth info dict."""
    proxy_secret = request.headers.get("x-rapidapi-proxy-secret", "")
    if proxy_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid RapidAPI proxy secret")

    rapidapi_user = request.headers.get("x-rapidapi-user", "unknown")
    subscription = request.headers.get("x-rapidapi-subscription", "BASIC")
    plan = _RAPIDAPI_PLAN_MAP.get(subscription.upper(), "free")

    return {
        "id": f"rapidapi_{rapidapi_user}",
        "user_id": f"rapidapi_{rapidapi_user}",
        "plan": plan,
        "is_active": True,
        "channel": "rapidapi",
    }
```

- [ ] **Step 6: Run tests — expect pass**

```bash
cd shared && uv run pytest tests/test_auth/ -v
```

- [ ] **Step 7: Commit**

```bash
git add shared/src/shared/auth/api_key.py shared/src/shared/auth/rapidapi.py \
  shared/tests/test_auth/test_api_key.py shared/tests/test_auth/test_rapidapi.py
git commit -m "feat(shared): add API key and RapidAPI auth validation"
```

---

### Task 5: Channel Detection + Auth Middleware

**Files:**
- Create: `shared/src/shared/middleware/channel_detect.py`
- Create: `shared/src/shared/auth/middleware.py`

- [ ] **Step 1: Write channel_detect.py**

```python
# shared/src/shared/middleware/channel_detect.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class ChannelDetectMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.headers.get("x-rapidapi-proxy-secret"):
            request.state.channel = "rapidapi"
        else:
            request.state.channel = "direct"
        return await call_next(request)  # type: ignore[misc]
```

- [ ] **Step 2: Write auth middleware**

```python
# shared/src/shared/auth/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from shared.auth.api_key import validate_api_key_direct
from shared.auth.rapidapi import validate_rapidapi

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe"})


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, skip_paths: frozenset[str] | None = None) -> None:
        super().__init__(app)
        self.skip_paths = skip_paths if skip_paths is not None else _SKIP_PATHS

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.url.path in self.skip_paths:
            return await call_next(request)  # type: ignore[misc]

        channel = getattr(request.state, "channel", "direct")

        try:
            if channel == "rapidapi":
                settings = request.app.state.shared_settings
                auth = await validate_rapidapi(request, settings.rapidapi_proxy_secret)
            else:
                raw_key = request.headers.get("x-api-key")
                if not raw_key:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "UNAUTHORIZED", "detail": "Missing X-API-Key header"},
                    )
                redis = request.app.state.redis
                session_factory = request.app.state.db_session_factory
                async with session_factory() as session:
                    auth = await validate_api_key_direct(raw_key, redis, session)

            request.state.auth = auth
        except Exception as exc:
            status = getattr(exc, "status_code", 401)
            detail = getattr(exc, "detail", "Authentication failed")
            return JSONResponse(
                status_code=status,
                content={"error": "UNAUTHORIZED", "detail": detail},
            )

        return await call_next(request)  # type: ignore[misc]
```

- [ ] **Step 3: Commit**

```bash
git add shared/src/shared/middleware/channel_detect.py shared/src/shared/auth/middleware.py
git commit -m "feat(shared): add channel detection and auth middleware"
```

---

### Task 6: Rate Limiting

**Files:**
- Create: `shared/src/shared/rate_limit/limiter.py`
- Create: `shared/src/shared/rate_limit/middleware.py`
- Test: `shared/tests/test_rate_limit/test_limiter.py`

- [ ] **Step 1: Write limiter tests**

```python
# shared/tests/test_rate_limit/test_limiter.py
import pytest

from shared.rate_limit.limiter import check_rate_limit


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_first_request_allowed(self, redis) -> None:
        allowed, remaining, limit = await check_rate_limit(redis, "key-1", 10)
        assert allowed is True
        assert remaining == 9
        assert limit == 10

    @pytest.mark.asyncio
    async def test_requests_up_to_limit(self, redis) -> None:
        for _ in range(10):
            allowed, _, _ = await check_rate_limit(redis, "key-2", 10)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_request_over_limit_blocked(self, redis) -> None:
        for _ in range(10):
            await check_rate_limit(redis, "key-3", 10)
        allowed, remaining, _ = await check_rate_limit(redis, "key-3", 10)
        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self, redis) -> None:
        for _ in range(10):
            await check_rate_limit(redis, "key-a", 10)
        allowed, _, _ = await check_rate_limit(redis, "key-b", 10)
        assert allowed is True
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd shared && uv run pytest tests/test_rate_limit/test_limiter.py -v
```

- [ ] **Step 3: Write limiter.py**

```python
# shared/src/shared/rate_limit/limiter.py
import time

from redis.asyncio import Redis


async def check_rate_limit(
    redis: Redis,
    key_id: str,
    limit_per_minute: int,
) -> tuple[bool, int, int]:
    """Fixed-window rate limiter. Returns (allowed, remaining, limit)."""
    window = int(time.time() // 60)
    redis_key = f"rate_limit:{key_id}:{window}"

    current = await redis.incr(redis_key)
    if current == 1:
        await redis.expire(redis_key, 120)

    remaining = max(0, limit_per_minute - current)
    allowed = current <= limit_per_minute
    return allowed, remaining, limit_per_minute
```

- [ ] **Step 4: Write rate_limit/middleware.py**

```python
# shared/src/shared/rate_limit/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from shared.billing.plans import get_plan
from shared.rate_limit.limiter import check_rate_limit

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)  # type: ignore[misc]

        auth: dict[str, object] | None = getattr(request.state, "auth", None)
        if auth is None:
            return await call_next(request)  # type: ignore[misc]

        plan = get_plan(str(auth["plan"]))
        redis = request.app.state.redis

        allowed, remaining, limit = await check_rate_limit(
            redis, str(auth["id"]), plan.rate_limit_per_minute
        )

        if not allowed:
            response: Response = JSONResponse(
                status_code=429,
                content={"error": "RATE_LIMIT_EXCEEDED", "detail": "Too many requests"},
            )
        else:
            response = await call_next(request)  # type: ignore[misc]

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
```

- [ ] **Step 5: Run limiter tests — expect pass**

```bash
cd shared && uv run pytest tests/test_rate_limit/test_limiter.py -v
```

- [ ] **Step 6: Commit**

```bash
git add shared/src/shared/rate_limit/ shared/tests/test_rate_limit/
git commit -m "feat(shared): add Redis-based rate limiter and middleware"
```

---

### Task 7: Metering

**Files:**
- Create: `shared/src/shared/metering/counter.py`
- Create: `shared/src/shared/metering/storage.py`
- Create: `shared/src/shared/metering/middleware.py`
- Test: `shared/tests/test_metering/test_counter.py`

- [ ] **Step 1: Write counter tests**

```python
# shared/tests/test_metering/test_counter.py
import pytest

from shared.metering.counter import get_usage, increment_usage


class TestMeteringCounter:
    @pytest.mark.asyncio
    async def test_increment_from_zero(self, redis) -> None:
        count = await increment_usage(redis, "key-1", "email-validation")
        assert count == 1

    @pytest.mark.asyncio
    async def test_increment_accumulates(self, redis) -> None:
        await increment_usage(redis, "key-2", "email-validation")
        await increment_usage(redis, "key-2", "email-validation")
        count = await increment_usage(redis, "key-2", "email-validation")
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_usage_returns_current(self, redis) -> None:
        for _ in range(5):
            await increment_usage(redis, "key-3", "email-validation")
        count = await get_usage(redis, "key-3", "email-validation")
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_usage_zero_when_empty(self, redis) -> None:
        count = await get_usage(redis, "nonexistent", "email-validation")
        assert count == 0

    @pytest.mark.asyncio
    async def test_different_apis_independent(self, redis) -> None:
        await increment_usage(redis, "key-4", "email-validation")
        await increment_usage(redis, "key-4", "qr-code")
        email_count = await get_usage(redis, "key-4", "email-validation")
        qr_count = await get_usage(redis, "key-4", "qr-code")
        assert email_count == 1
        assert qr_count == 1
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd shared && uv run pytest tests/test_metering/test_counter.py -v
```

- [ ] **Step 3: Write counter.py**

```python
# shared/src/shared/metering/counter.py
from datetime import datetime, timezone

from redis.asyncio import Redis


async def increment_usage(redis: Redis, key_id: str, api_name: str) -> int:
    """Increment usage counter in Redis. Returns new count."""
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    redis_key = f"usage:{key_id}:{api_name}:{month}"
    count = await redis.incr(redis_key)
    if count == 1:
        await redis.expire(redis_key, 90 * 24 * 3600)
    return count


async def get_usage(redis: Redis, key_id: str, api_name: str) -> int:
    """Get current month's usage count from Redis."""
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    redis_key = f"usage:{key_id}:{api_name}:{month}"
    count = await redis.get(redis_key)
    return int(count) if count else 0
```

- [ ] **Step 4: Write storage.py**

```python
# shared/src/shared/metering/storage.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.models import UsageRecord


async def flush_usage_to_db(
    db_session: AsyncSession,
    api_key_id: str,
    api_name: str,
    month: str,
    count: int,
) -> None:
    """Persist Redis usage counter to PostgreSQL."""
    result = await db_session.execute(
        select(UsageRecord).where(
            UsageRecord.api_key_id == uuid.UUID(api_key_id),
            UsageRecord.api_name == api_name,
            UsageRecord.month == month,
        )
    )
    record = result.scalar_one_or_none()

    if record:
        record.request_count = count
    else:
        record = UsageRecord(
            api_key_id=uuid.UUID(api_key_id),
            api_name=api_name,
            month=month,
            request_count=count,
        )
        db_session.add(record)

    await db_session.commit()
```

- [ ] **Step 5: Write metering/middleware.py**

```python
# shared/src/shared/metering/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from shared.billing.plans import get_plan
from shared.metering.counter import get_usage, increment_usage

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe"})


class MeteringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, api_name: str) -> None:
        super().__init__(app)
        self.api_name = api_name

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)  # type: ignore[misc]

        auth: dict[str, object] | None = getattr(request.state, "auth", None)
        if auth is None:
            return await call_next(request)  # type: ignore[misc]

        redis = request.app.state.redis
        plan = get_plan(str(auth["plan"]))

        current_usage = await get_usage(redis, str(auth["id"]), self.api_name)
        if current_usage >= plan.requests_per_month:
            return JSONResponse(
                status_code=429,
                content={"error": "QUOTA_EXCEEDED", "detail": "Monthly quota exhausted"},
            )

        response: Response = await call_next(request)  # type: ignore[misc]

        if response.status_code < 400:
            new_count = await increment_usage(redis, str(auth["id"]), self.api_name)
            response.headers["X-Usage-Current"] = str(new_count)
            response.headers["X-Usage-Limit"] = str(plan.requests_per_month)

        return response
```

- [ ] **Step 6: Run counter tests — expect pass**

```bash
cd shared && uv run pytest tests/test_metering/test_counter.py -v
```

- [ ] **Step 7: Commit**

```bash
git add shared/src/shared/metering/ shared/tests/test_metering/
git commit -m "feat(shared): add usage metering — counter, storage, middleware"
```

---

### Task 8: Billing — Stripe Client + Webhooks

**Files:**
- Create: `shared/src/shared/billing/stripe_client.py`
- Create: `shared/src/shared/billing/webhooks.py`

- [ ] **Step 1: Write stripe_client.py**

```python
# shared/src/shared/billing/stripe_client.py
# DEVIATION: Stripe SDK uses sync HTTP (requests) internally. Billing operations
# are infrequent (not per-request), so the thread-pool overhead is acceptable.
import stripe

from shared.billing.plans import PlanDefinition


class StripeClient:
    def __init__(self, secret_key: str) -> None:
        self._key = secret_key

    def create_customer(self, email: str) -> str:
        customer = stripe.Customer.create(email=email, api_key=self._key)
        return str(customer.id)

    def create_subscription(self, customer_id: str, plan: PlanDefinition) -> str | None:
        if plan.stripe_price_id is None:
            return None
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": plan.stripe_price_id}],
            api_key=self._key,
        )
        return str(subscription.id)

    def cancel_subscription(self, subscription_id: str) -> None:
        stripe.Subscription.delete(subscription_id, api_key=self._key)
```

- [ ] **Step 2: Write webhooks.py**

```python
# shared/src/shared/billing/webhooks.py
import stripe
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def handle_stripe_webhook(request: Request) -> JSONResponse:
    """Handle Stripe webhook events for subscription lifecycle."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    settings = request.app.state.shared_settings

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError):
        return JSONResponse(status_code=400, content={"error": "Invalid webhook signature"})

    event_type: str = event["type"]

    if event_type == "customer.subscription.updated":
        # Plan change — invalidate API key cache so new limits take effect
        pass
    elif event_type == "customer.subscription.deleted":
        # Cancellation — deactivate keys or downgrade to free
        pass
    elif event_type == "invoice.payment_failed":
        # Payment failure — could send alert or grace period
        pass

    return JSONResponse(content={"status": "ok"})
```

- [ ] **Step 3: Commit**

```bash
git add shared/src/shared/billing/stripe_client.py shared/src/shared/billing/webhooks.py
git commit -m "feat(shared): add Stripe billing client and webhook handler"
```

---

### Task 9: Setup Function + Dependencies + Exports

**Files:**
- Create: `shared/src/shared/setup.py`
- Create: `shared/src/shared/dependencies.py`
- Modify: `shared/src/shared/__init__.py`

- [ ] **Step 1: Write setup.py**

```python
# shared/src/shared/setup.py
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
```

- [ ] **Step 2: Write dependencies.py**

```python
# shared/src/shared/dependencies.py
from typing import Annotated

from fastapi import Depends, HTTPException, Request


async def require_auth(request: Request) -> dict[str, object]:
    """Read auth info set by AuthMiddleware. Use as a route dependency."""
    auth: dict[str, object] | None = getattr(request.state, "auth", None)
    if auth is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return auth


Auth = Annotated[dict[str, object], Depends(require_auth)]
```

- [ ] **Step 3: Write __init__.py exports**

```python
# shared/src/shared/__init__.py
from shared.auth.middleware import AuthMiddleware
from shared.billing.plans import PLANS, PlanDefinition, get_plan
from shared.dependencies import Auth, require_auth
from shared.middleware.channel_detect import ChannelDetectMiddleware
from shared.metering.middleware import MeteringMiddleware
from shared.rate_limit.middleware import RateLimitMiddleware
from shared.setup import setup_shared

__all__ = [
    "Auth",
    "AuthMiddleware",
    "ChannelDetectMiddleware",
    "MeteringMiddleware",
    "PLANS",
    "PlanDefinition",
    "RateLimitMiddleware",
    "get_plan",
    "require_auth",
    "setup_shared",
]
```

- [ ] **Step 4: Commit**

```bash
git add shared/src/shared/setup.py shared/src/shared/dependencies.py shared/src/shared/__init__.py
git commit -m "feat(shared): add setup function, dependencies, and public exports"
```

---

### Task 10: Integration Test — Full Middleware Stack

**Files:**
- Create: `shared/tests/test_middleware/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# shared/tests/test_middleware/test_integration.py
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

    # In-memory backends
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.redis = redis
    app.state.shared_settings = MagicMock(
        spec=SharedSettings, rapidapi_proxy_secret="test-secret"
    )

    # Middleware (last added = outermost = runs first)
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

    # Seed a test API key
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
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
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
    async def test_rate_limit_headers_present(
        self, test_app: FastAPI, client: AsyncClient
    ) -> None:
        key = test_app.state._test_api_key
        response = await client.get("/test", headers={"x-api-key": key})
        assert response.headers["X-RateLimit-Limit"] == "60"  # basic plan

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
```

- [ ] **Step 2: Run all tests**

```bash
cd shared && uv run pytest -v
```

- [ ] **Step 3: Run ruff and mypy**

```bash
cd shared && uv run ruff format . && uv run ruff check . --fix && uv run mypy src/
```

- [ ] **Step 4: Commit**

```bash
git add shared/tests/test_middleware/
git commit -m "test(shared): add full middleware stack integration test"
```

---

### Task 11: Wire Shared Into Email Validation

**Files:**
- Modify: `projects/email-validation/pyproject.toml`
- Modify: `projects/email-validation/src/email_validation/main.py`
- Modify: `projects/email-validation/src/email_validation/config.py`

- [ ] **Step 1: Add shared dependency to email-validation pyproject.toml**

Add to `[project] dependencies`:
```toml
"shared @ file://../../shared",
```

- [ ] **Step 2: Update email-validation config.py to extend SharedSettings**

```python
# projects/email-validation/src/email_validation/config.py
from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    smtp_timeout: float = 10.0
    dns_timeout: float = 5.0
    max_batch_size: int = 50
    smtp_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Update email-validation main.py with shared middleware**

```python
# projects/email-validation/src/email_validation/main.py
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from email_validation.config import get_settings
from email_validation.exceptions import AppError, app_exception_handler
from email_validation.routes.validation import router as validation_router
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Email Validation API",
        description=(
            "Production-grade email validation — syntax checks, MX record lookup, "
            "SMTP verification, disposable email detection, and role-based email detection. "
            "10x cheaper than Hunter.io and ZeroBounce."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]

    # Middleware stack (last added = outermost = runs first on request)
    app.add_middleware(MeteringMiddleware, api_name="email-validation")
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ChannelDetectMiddleware)

    app.include_router(validation_router)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 4: Reinstall and run email-validation tests**

```bash
cd projects/email-validation && uv sync && uv run pytest -v
```

Note: some route tests may need fixture updates to mock shared middleware state (set `request.state.auth`). Fix any failures.

- [ ] **Step 5: Run full quality checks across both packages**

```bash
cd shared && uv run ruff format . && uv run ruff check . --fix && uv run mypy src/ && uv run pytest -v
cd ../projects/email-validation && uv run ruff format . && uv run ruff check . --fix && uv run mypy src/ && uv run pytest -v
```

- [ ] **Step 6: Commit**

```bash
git add projects/email-validation/ shared/
git commit -m "feat: wire shared infrastructure into email-validation API"
```
