from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)

from template_api.config import get_settings
from template_api.exceptions import AppError, app_exception_handler
from template_api.middleware.cookie_auth import CookieToHeaderMiddleware
from template_api.routes.api import router as api_router
from template_api.routes.ui import router as ui_router

_STATIC_DIR = Path(__file__).resolve().parent / "static"

_AUTH_SKIP_PATHS = frozenset(
    {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/webhooks/stripe",
        "/ui/login",
        "/ui/logout",
    }
)

_QUOTA_SKIP_PREFIXES = ("/ui/", "/static/")
_AUTH_SKIP_PREFIXES = ("/static/",)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]

    app.add_middleware(
        MeteringMiddleware,
        api_name="template-api",
        skip_prefixes=_QUOTA_SKIP_PREFIXES,
    )
    app.add_middleware(RateLimitMiddleware, skip_prefixes=_QUOTA_SKIP_PREFIXES)
    app.add_middleware(
        AuthMiddleware,
        skip_paths=_AUTH_SKIP_PATHS,
        skip_prefixes=_AUTH_SKIP_PREFIXES,
    )
    app.add_middleware(ChannelDetectMiddleware)
    app.add_middleware(CookieToHeaderMiddleware, secret_key=settings.cookie_secret_key)

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    app.include_router(api_router)
    app.include_router(ui_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse("/ui/login", status_code=302)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
