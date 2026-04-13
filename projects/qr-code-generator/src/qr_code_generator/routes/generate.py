import re
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from qr_code_generator.config import Settings, get_settings
from qr_code_generator.exceptions import (
    InvalidColorError,
    LogoFormatError,
    LogoSvgConflictError,
    LogoTooLargeError,
)
from qr_code_generator.schemas.generate import QRCodeRequest
from qr_code_generator.services.generator import generate_qr

router = APIRouter(prefix="/v1/generate", tags=["generate"])

SettingsDep = Annotated[Settings, Depends(get_settings)]

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

_ALLOWED_LOGO_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})

_MEDIA_TYPES: dict[str, str] = {
    "png": "image/png",
    "svg": "image/svg+xml",
}


def _validate_color(color: str) -> None:
    if not _HEX_COLOR_RE.match(color):
        raise InvalidColorError(color)


async def _read_logo(
    logo: UploadFile | None,
    output_format: str,
    max_size: int,
) -> bytes | None:
    if logo is None or not logo.filename:
        return None
    if output_format == "svg":
        raise LogoSvgConflictError()
    logo_bytes = await logo.read()
    if len(logo_bytes) > max_size:
        raise LogoTooLargeError(max_size)
    content_type = logo.content_type or ""
    if content_type not in _ALLOWED_LOGO_TYPES:
        raise LogoFormatError(content_type)
    return logo_bytes


@router.post("/qrcode")
async def generate_qrcode(
    settings: SettingsDep,
    data: Annotated[str, Form(min_length=1, max_length=2953)],
    fmt: Annotated[Literal["png", "svg"], Form(alias="format")] = "png",
    size: Annotated[int, Form(ge=50, le=2000)] = 300,
    error_correction: Annotated[Literal["L", "M", "Q", "H"], Form()] = "M",
    border: Annotated[int, Form(ge=0, le=10)] = 4,
    foreground_color: Annotated[str, Form()] = "#000000",
    background_color: Annotated[str, Form()] = "#FFFFFF",
    logo: UploadFile | None = None,
    logo_size_ratio: Annotated[float, Form(ge=0.1, le=0.4)] = 0.25,
) -> Response:
    """Generate a QR code with optional logo embedding."""
    _validate_color(foreground_color)
    _validate_color(background_color)

    logo_bytes = await _read_logo(logo, fmt, settings.max_logo_size)

    params = QRCodeRequest(
        data=data,
        format=fmt,
        size=size,
        error_correction=error_correction,
        border=border,
        foreground_color=foreground_color,
        background_color=background_color,
        logo_size_ratio=logo_size_ratio,
    )

    content = generate_qr(params, logo_bytes=logo_bytes)

    return Response(
        content=content,
        media_type=_MEDIA_TYPES[params.format],
        headers={"Content-Disposition": f"inline; filename=qrcode.{params.format}"},
    )
