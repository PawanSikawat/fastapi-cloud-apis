from datetime import UTC, datetime

from redis.asyncio import Redis


async def increment_usage(redis: Redis, key_id: str, api_name: str) -> int:
    """Increment usage counter in Redis. Returns new count."""
    month = datetime.now(UTC).strftime("%Y-%m")
    redis_key = f"usage:{key_id}:{api_name}:{month}"
    count = int(await redis.incr(redis_key))
    if count == 1:
        await redis.expire(redis_key, 90 * 24 * 3600)
    return count


async def get_usage(redis: Redis, key_id: str, api_name: str) -> int:
    """Get current month's usage count from Redis."""
    month = datetime.now(UTC).strftime("%Y-%m")
    redis_key = f"usage:{key_id}:{api_name}:{month}"
    count = await redis.get(redis_key)
    return int(count) if count else 0
