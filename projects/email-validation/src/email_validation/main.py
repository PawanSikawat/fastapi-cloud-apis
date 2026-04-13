from fastapi import FastAPI

from email_validation.exceptions import AppError, app_exception_handler
from email_validation.routes.validation import router as validation_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Email Validation API",
        description=(
            "Production-grade email validation — syntax checks, MX record lookup, "
            "SMTP verification, disposable email detection, and role-based email detection. "
            "10x cheaper than Hunter.io and ZeroBounce."
        ),
        version="0.1.0",
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]
    app.include_router(validation_router)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
