from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)

from email_validation.config import get_settings
from email_validation.exceptions import AppError, app_exception_handler
from email_validation.routes.validation import router as validation_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        yield


def create_app() -> FastAPI:
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
    app.add_middleware(MeteringMiddleware, api_name="email-validation")
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ChannelDetectMiddleware)

    app.include_router(validation_router)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
