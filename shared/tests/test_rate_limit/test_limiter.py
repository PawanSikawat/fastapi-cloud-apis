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
