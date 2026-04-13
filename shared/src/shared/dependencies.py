from typing import Annotated

from fastapi import Depends, HTTPException, Request


async def require_auth(request: Request) -> dict[str, object]:
    """Read auth info set by AuthMiddleware. Use as a route dependency."""
    auth: dict[str, object] | None = getattr(request.state, "auth", None)
    if auth is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return auth


Auth = Annotated[dict[str, object], Depends(require_auth)]
