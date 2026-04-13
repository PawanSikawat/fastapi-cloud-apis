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
