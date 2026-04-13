import base64
import hashlib
import io
import json

import segno
from PIL import Image
from redis.asyncio import Redis

from qr_code_generator.exceptions import InvalidDataError
from qr_code_generator.schemas.generate import QRCodeRequest


def _compute_scale(qr: segno.QRCode, target_size: int, border: int) -> int:
    """Calculate scale factor to approximate the target output dimension.

    Uses raw module count (border=0) so that border modules are additive.
    Scale is capped at floor(target/raw) to prevent output exceeding target
    when border=0, while using ceiling division against total modules to
    produce a larger image when border is added (satisfying the invariant
    that a wider border produces a larger image at the same target size).
    """
    raw_modules: int = int(qr.symbol_size(border=0)[0])
    total_modules: int = raw_modules + 2 * border
    # Ceiling division via negation: -(-a // b) avoids float intermediates.
    scale: int = min(target_size // raw_modules, -(-target_size // total_modules))
    return max(1, scale)


def _composite_logo(qr_png: bytes, logo_bytes: bytes, ratio: float) -> bytes:
    """Paste a logo image centered on the QR code PNG."""
    qr_img = Image.open(io.BytesIO(qr_png)).convert("RGBA")
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

    logo_max_size = int(qr_img.width * ratio)
    logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)

    x = (qr_img.width - logo.width) // 2
    y = (qr_img.height - logo.height) // 2
    qr_img.paste(logo, (x, y), logo)

    output = io.BytesIO()
    qr_img.save(output, format="PNG")
    return output.getvalue()


def generate_qr(
    params: QRCodeRequest,
    logo_bytes: bytes | None = None,
) -> bytes:
    """Generate a QR code image. Returns PNG or SVG bytes."""
    error_level = "H" if logo_bytes else params.error_correction

    try:
        qr = segno.make(params.data, error=error_level)
    except segno.DataOverflowError:
        raise InvalidDataError(f"data too long for error correction level {error_level}") from None

    scale = _compute_scale(qr, params.size, params.border)

    buffer = io.BytesIO()
    qr.save(
        buffer,
        kind=params.format,
        scale=scale,
        border=params.border,
        dark=params.foreground_color,
        light=params.background_color,
    )
    content = buffer.getvalue()

    if logo_bytes and params.format == "png":
        content = _composite_logo(content, logo_bytes, params.logo_size_ratio)

    return content


def _cache_key(params: QRCodeRequest, logo_bytes: bytes | None) -> str:
    """Compute deterministic cache key from all input parameters."""
    payload = json.dumps(params.model_dump(mode="json"), sort_keys=True)
    if logo_bytes:
        payload += hashlib.sha256(logo_bytes).hexdigest()
    return f"qr:{hashlib.sha256(payload.encode()).hexdigest()}"


async def generate_qr_cached(
    params: QRCodeRequest,
    logo_bytes: bytes | None,
    redis: Redis,
    cache_ttl: int,
) -> bytes:
    """Generate QR code with Redis caching."""
    key = _cache_key(params, logo_bytes)
    cached = await redis.get(key)
    if cached:
        return base64.b64decode(cached)

    content = generate_qr(params, logo_bytes=logo_bytes)
    await redis.setex(key, cache_ttl, base64.b64encode(content).decode())
    return content
