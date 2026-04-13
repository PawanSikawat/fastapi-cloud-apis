from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from shared.billing.plans import get_plan
from shared.metering.counter import get_usage, increment_usage

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe"})


class MeteringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, api_name: str, skip_prefixes: tuple[str, ...] = ()) -> None:
        super().__init__(app)
        self.api_name = api_name
        self.skip_prefixes = skip_prefixes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in _SKIP_PATHS or path.startswith(self.skip_prefixes):
            return await call_next(request)

        auth: dict[str, object] | None = getattr(request.state, "auth", None)
        if auth is None:
            return await call_next(request)

        redis = request.app.state.redis
        plan = get_plan(str(auth["plan"]))

        current_usage = await get_usage(redis, str(auth["id"]), self.api_name)
        if current_usage >= plan.requests_per_month:
            return JSONResponse(
                status_code=429,
                content={"error": "QUOTA_EXCEEDED", "detail": "Monthly quota exhausted"},
            )

        response: Response = await call_next(request)

        if response.status_code < 400:
            new_count = await increment_usage(redis, str(auth["id"]), self.api_name)
            response.headers["X-Usage-Current"] = str(new_count)
            response.headers["X-Usage-Limit"] = str(plan.requests_per_month)

        return response
