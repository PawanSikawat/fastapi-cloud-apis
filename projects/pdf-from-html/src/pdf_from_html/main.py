from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
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
from pdf_from_html.routes.generate import router as generate_router
from pdf_from_html.services.browser_pool import BrowserPool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        pw = await async_playwright().start()
        browser = await pw.chromium.launch()
        app.state.browser_pool = BrowserPool(browser, settings.browser_pool_size)
        try:
            yield
        finally:
            await app.state.browser_pool.close()
            await pw.stop()


def create_app() -> FastAPI:
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
    app.add_middleware(MeteringMiddleware, api_name="pdf-from-html")
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ChannelDetectMiddleware)

    app.include_router(generate_router)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
