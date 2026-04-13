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
