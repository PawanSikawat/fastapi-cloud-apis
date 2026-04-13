from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class InvalidDataError(AppError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=422,
            detail=f"Invalid QR data: {reason}",
            error_code="INVALID_DATA",
        )


class InvalidColorError(AppError):
    def __init__(self, color: str) -> None:
        super().__init__(
            status_code=422,
            detail=f"Invalid hex color: {color!r} — expected format #RRGGBB",
            error_code="INVALID_COLOR",
        )


class LogoTooLargeError(AppError):
    def __init__(self, max_size: int) -> None:
        super().__init__(
            status_code=422,
            detail=f"Logo file exceeds maximum size of {max_size} bytes",
            error_code="LOGO_TOO_LARGE",
        )


class LogoFormatError(AppError):
    def __init__(self, content_type: str) -> None:
        super().__init__(
            status_code=422,
            detail=(
                f"Unsupported logo format: {content_type!r}"
                " — accepted: image/png, image/jpeg, image/webp"
            ),
            error_code="LOGO_FORMAT_UNSUPPORTED",
        )


class LogoSvgConflictError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=422,
            detail="Cannot embed a logo in SVG output — use PNG format instead",
            error_code="LOGO_SVG_CONFLICT",
        )


async def app_exception_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.detail},
    )
