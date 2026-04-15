from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class InvalidInputError(AppError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=422,
            detail=f"Invalid input: {reason}",
            error_code="INVALID_INPUT",
        )


async def app_exception_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.detail},
    )
