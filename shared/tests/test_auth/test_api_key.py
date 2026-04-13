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
        from shared.auth.key_utils import hash_api_key

        cached = await redis.get(f"api_key:{hash_api_key(raw_key)}")
        assert cached is not None
