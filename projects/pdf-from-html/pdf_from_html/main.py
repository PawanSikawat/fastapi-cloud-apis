import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)

from pdf_from_html.config import get_settings
from pdf_from_html.exceptions import AppError, app_exception_handler
from pdf_from_html.middleware.cookie_auth import CookieToHeaderMiddleware
from pdf_from_html.routes.generate import router as generate_router
from pdf_from_html.routes.ui import router as ui_router
from pdf_from_html.services.browser_pool import BrowserPool

_STATIC_DIR = Path(__file__).resolve().parent / "static"

# Auth skip paths: default shared paths + public UI paths
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

# Rate-limit and metering skip prefixes: UI pages and static assets
# should not consume API quota — only /v1/* endpoints are metered.
_QUOTA_SKIP_PREFIXES = ("/ui/", "/static/")

# Auth skip prefixes: static assets don't require authentication
_AUTH_SKIP_PREFIXES = ("/static/",)


async def _ensure_chromium() -> None:
    """Download Chromium if the binary is missing (first deploy on FastAPI Cloud)."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "playwright",
        "install",
        "chromium",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Chromium install failed: {stderr.decode()}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        await _ensure_chromium()
        pw = await async_playwright().start()
        browser = await pw.chromium.launch()
        app.state.browser_pool = BrowserPool(browser, settings.browser_pool_size)
        try:
            yield
        finally:
            await app.state.browser_pool.close()
            await pw.stop()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PDF from HTML API",
        description=(
            "Generate PDFs from raw HTML or URLs using Chromium. "
            "Pixel-perfect rendering with full CSS3 and JavaScript support."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]

    # Middleware stack (last added = outermost = runs first on request)
    # 5. MeteringMiddleware — innermost, tracks API usage
    app.add_middleware(
        MeteringMiddleware,
        api_name="pdf-from-html",
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
    app.include_router(generate_router)
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
