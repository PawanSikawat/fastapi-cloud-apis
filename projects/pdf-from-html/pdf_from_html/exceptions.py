from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class InvalidURLError(AppError):
    def __init__(self, url: str) -> None:
        super().__init__(
            status_code=422,
            detail=f"Invalid URL: must use http or https scheme — got {url!r}",
            error_code="INVALID_URL",
        )


class ContentTooLargeError(AppError):
    def __init__(self, max_size: int) -> None:
        super().__init__(
            status_code=422,
            detail=f"Content exceeds maximum size of {max_size} bytes",
            error_code="CONTENT_TOO_LARGE",
        )


class RenderTimeoutError(AppError):
    def __init__(self, timeout: float) -> None:
        super().__init__(
            status_code=504,
            detail=f"Render timed out after {timeout} seconds",
            error_code="RENDER_TIMEOUT",
        )


class RenderFailedError(AppError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=502,
            detail=f"Render failed: {reason}",
            error_code="RENDER_FAILED",
        )


async def app_exception_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.detail},
    )
