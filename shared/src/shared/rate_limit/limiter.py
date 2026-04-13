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
