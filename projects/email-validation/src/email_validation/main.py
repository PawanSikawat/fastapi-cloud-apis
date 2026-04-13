from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)

from email_validation.config import get_settings
from email_validation.exceptions import AppError, app_exception_handler
from email_validation.middleware.cookie_auth import CookieToHeaderMiddleware
from email_validation.routes.ui import router as ui_router
from email_validation.routes.validation import router as validation_router

_STATIC_DIR = Path(__file__).resolve().parent / "static"

# Auth skip paths: default shared paths + public UI paths
_AUTH_SKIP_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/webhooks/stripe",
        "/ui/login",
    }
)

# Rate-limit and metering skip prefixes: UI pages and static assets
# should not consume API quota — only /v1/* endpoints are metered.
_QUOTA_SKIP_PREFIXES = ("/ui/", "/static/")

# Auth skip prefixes: static assets don't require authentication
_AUTH_SKIP_PREFIXES = ("/static/",)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Email Validation API",
        description=(
            "Production-grade email validation — syntax checks, MX record lookup, "
            "SMTP verification, disposable email detection, and role-based email detection. "
            "10x cheaper than Hunter.io and ZeroBounce."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]

    # Middleware stack (last added = outermost = runs first on request)
    # 5. MeteringMiddleware — innermost, tracks API usage
    app.add_middleware(
        MeteringMiddleware,
        api_name="email-validation",
        skip_prefixes=_QUOTA_SKIP_PREFIXES,
    )
    # 4. RateLimitMiddleware — enforces per-minute rate limits
    app.add_middleware(RateLimitMiddleware, skip_prefixes=_QUOTA_SKIP_PREFIXES)
    # 3. AuthMiddleware — validates API key (from header or injected by cookie middleware)
    app.add_middleware(
        AuthMiddleware,
        skip_paths=_AUTH_SKIP_PATHS,
        skip_prefixes=_AUTH_SKIP_PREFIXES,
    )
    # 2. ChannelDetectMiddleware — sets request.state.channel
    app.add_middleware(ChannelDetectMiddleware)
    # 1. CookieToHeaderMiddleware — outermost, reads cookie and injects x-api-key header
    app.add_middleware(CookieToHeaderMiddleware, secret_key=settings.cookie_secret_key)

    # Static files
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Routers
    app.include_router(validation_router)
    app.include_router(ui_router)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
