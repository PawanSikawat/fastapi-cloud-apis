from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from shared.billing.plans import get_plan
from shared.rate_limit.limiter import check_rate_limit

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, skip_prefixes: tuple[str, ...] = ()) -> None:
        super().__init__(app)
        self.skip_prefixes = skip_prefixes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in _SKIP_PATHS or path.startswith(self.skip_prefixes):
            return await call_next(request)

        auth: dict[str, object] | None = getattr(request.state, "auth", None)
        if auth is None:
            return await call_next(request)

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
            response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
