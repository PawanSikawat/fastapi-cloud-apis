from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from shared.auth.api_key import validate_api_key_direct
from shared.auth.rapidapi import validate_rapidapi

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe"})


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        skip_paths: frozenset[str] | None = None,
        skip_prefixes: tuple[str, ...] = (),
    ) -> None:
        super().__init__(app)
        self.skip_paths = skip_paths if skip_paths is not None else _SKIP_PATHS
        self.skip_prefixes = skip_prefixes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in self.skip_paths or path.startswith(self.skip_prefixes):
            return await call_next(request)

        channel = getattr(request.state, "channel", "direct")

        try:
            if channel == "rapidapi":
                settings = request.app.state.shared_settings
                auth = await validate_rapidapi(request, settings.rapidapi_proxy_secret)
            else:
                raw_key = request.headers.get("x-api-key")
                if not raw_key:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "UNAUTHORIZED", "detail": "Missing X-API-Key header"},
                    )
                redis = request.app.state.redis
                session_factory = request.app.state.db_session_factory
                async with session_factory() as session:
                    auth = await validate_api_key_direct(raw_key, redis, session)

            request.state.auth = auth
        except Exception as exc:
            status = getattr(exc, "status_code", 401)
            detail = getattr(exc, "detail", "Authentication failed")
            return JSONResponse(
                status_code=status,
                content={"error": "UNAUTHORIZED", "detail": detail},
            )

        return await call_next(request)
