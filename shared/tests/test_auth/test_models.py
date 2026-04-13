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
