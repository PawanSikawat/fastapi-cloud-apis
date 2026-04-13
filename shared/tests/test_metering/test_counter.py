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
