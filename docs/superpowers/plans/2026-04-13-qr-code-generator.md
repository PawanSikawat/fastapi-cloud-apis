# QR Code Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a QR code generation API with optional logo embedding, PNG/SVG output, Redis caching, and a web UI.

**Architecture:** Single `POST /v1/generate/qrcode` endpoint accepting multipart form data. `segno` library generates QR codes in PNG/SVG. `pillow` composites logos onto PNG output. Redis caches results by parameter hash. Web UI with Pico CSS + HTMX follows existing project conventions.

**Tech Stack:** FastAPI, segno, Pillow, python-multipart, Redis (shared infra), Pico CSS, HTMX, Jinja2.

**Spec:** `docs/superpowers/specs/2026-04-13-qr-code-generator-design.md`

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `projects/qr-code-generator/pyproject.toml`
- Create: `projects/qr-code-generator/src/qr_code_generator/__init__.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/routes/__init__.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/schemas/__init__.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/services/__init__.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/middleware/__init__.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/dependencies/__init__.py`
- Create: `projects/qr-code-generator/tests/__init__.py`
- Create: `projects/qr-code-generator/tests/test_routes/__init__.py`
- Create: `projects/qr-code-generator/tests/test_services/__init__.py`
- Create: `projects/qr-code-generator/tests/test_schemas/__init__.py`
- Copy: `projects/pdf-from-html/src/pdf_from_html/static/css/pico.min.css` → `projects/qr-code-generator/src/qr_code_generator/static/css/pico.min.css`
- Copy: `projects/pdf-from-html/src/pdf_from_html/static/js/htmx.min.js` → `projects/qr-code-generator/src/qr_code_generator/static/js/htmx.min.js`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "qr-code-generator"
version = "0.1.0"
description = "QR Code Generator API — generate QR codes with optional logo embedding"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.7.0",
    "segno>=1.6.0",
    "pillow>=11.0.0",
    "python-multipart>=0.0.18",
    "jinja2>=3.1.0",
    "itsdangerous>=2.2.0",
    "shared",
]

[tool.hatch.build.targets.wheel]
packages = ["src/qr_code_generator"]

[tool.hatch.metadata]
allow-direct-references = true

[tool.uv.sources]
shared = { path = "../../shared", editable = true }

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "pytest-cov>=6.0.0",
    "mypy>=1.14.0",
    "ruff>=0.9.0",
    "fakeredis>=2.26.0",
    "aiosqlite>=0.21.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "A", "SIM", "TCH"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
```

- [ ] **Step 2: Create directory structure**

Create all `__init__.py` files (empty) at the paths listed above. Also create the `static/css/` and `static/js/` directories.

- [ ] **Step 3: Copy static assets**

```bash
cp projects/pdf-from-html/src/pdf_from_html/static/css/pico.min.css projects/qr-code-generator/src/qr_code_generator/static/css/pico.min.css
cp projects/pdf-from-html/src/pdf_from_html/static/js/htmx.min.js projects/qr-code-generator/src/qr_code_generator/static/js/htmx.min.js
```

- [ ] **Step 4: Install dependencies**

```bash
cd projects/qr-code-generator && uv sync
```

Expected: successful install, no errors.

- [ ] **Step 5: Commit**

```bash
git add projects/qr-code-generator/
git commit -m "chore(qr-code-generator): scaffold project structure and dependencies"
```

---

### Task 2: Configuration and exceptions

**Files:**
- Create: `projects/qr-code-generator/src/qr_code_generator/config.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/exceptions.py`

- [ ] **Step 1: Create config.py**

```python
from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    cache_ttl: int = 86400
    max_logo_size: int = 512_000
    max_data_length: int = 2953
    cookie_secret_key: str = "dev-secret-change-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Create exceptions.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/config.py projects/qr-code-generator/src/qr_code_generator/exceptions.py
git commit -m "feat(qr-code-generator): add configuration and exception classes"
```

---

### Task 3: Request schema (TDD)

**Files:**
- Test: `projects/qr-code-generator/tests/test_schemas/test_generate.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/schemas/generate.py`

- [ ] **Step 1: Write schema tests**

```python
import pytest
from pydantic import ValidationError


class TestQRCodeRequestDefaults:
    def test_minimal_request(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="hello")
        assert req.data == "hello"
        assert req.format == "png"
        assert req.size == 300
        assert req.error_correction == "M"
        assert req.border == 4
        assert req.foreground_color == "#000000"
        assert req.background_color == "#ffffff"
        assert req.logo_size_ratio == 0.25


class TestQRCodeRequestColorValidation:
    def test_valid_hex_colors(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(
            data="test",
            foreground_color="#FF5733",
            background_color="#00aaFF",
        )
        assert req.foreground_color == "#ff5733"
        assert req.background_color == "#00aaff"

    def test_invalid_foreground_color(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="foreground_color"):
            QRCodeRequest(data="test", foreground_color="notacolor")

    def test_invalid_background_color_short(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="background_color"):
            QRCodeRequest(data="test", background_color="#FFF")

    def test_color_without_hash(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="foreground_color"):
            QRCodeRequest(data="test", foreground_color="000000")


class TestQRCodeRequestBoundaries:
    def test_size_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", size=50)
        assert req.size == 50

    def test_size_below_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="size"):
            QRCodeRequest(data="test", size=49)

    def test_size_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", size=2000)
        assert req.size == 2000

    def test_size_above_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="size"):
            QRCodeRequest(data="test", size=2001)

    def test_border_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", border=0)
        assert req.border == 0

    def test_border_above_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="border"):
            QRCodeRequest(data="test", border=11)

    def test_logo_size_ratio_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", logo_size_ratio=0.1)
        assert req.logo_size_ratio == 0.1

    def test_logo_size_ratio_below_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="logo_size_ratio"):
            QRCodeRequest(data="test", logo_size_ratio=0.05)

    def test_logo_size_ratio_above_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="logo_size_ratio"):
            QRCodeRequest(data="test", logo_size_ratio=0.5)

    def test_empty_data(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="data"):
            QRCodeRequest(data="")


class TestQRCodeRequestFormat:
    def test_png_format(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", format="png")
        assert req.format == "png"

    def test_svg_format(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", format="svg")
        assert req.format == "svg"

    def test_invalid_format(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="format"):
            QRCodeRequest(data="test", format="pdf")


class TestQRCodeRequestErrorCorrection:
    @pytest.mark.parametrize("level", ["L", "M", "Q", "H"])
    def test_valid_levels(self, level: str) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", error_correction=level)
        assert req.error_correction == level

    def test_invalid_level(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="error_correction"):
            QRCodeRequest(data="test", error_correction="X")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_schemas/test_generate.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'qr_code_generator.schemas.generate'`

- [ ] **Step 3: Implement schema**

```python
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class QRCodeRequest(BaseModel):
    data: str = Field(min_length=1, max_length=2953)
    format: Literal["png", "svg"] = "png"
    size: int = Field(default=300, ge=50, le=2000)
    error_correction: Literal["L", "M", "Q", "H"] = "M"
    border: int = Field(default=4, ge=0, le=10)
    foreground_color: str = Field(default="#000000")
    background_color: str = Field(default="#FFFFFF")
    logo_size_ratio: float = Field(default=0.25, ge=0.1, le=0.4)

    @field_validator("foreground_color", "background_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not _HEX_COLOR_RE.match(v):
            msg = f"Invalid hex color: {v!r} — expected format #RRGGBB"
            raise ValueError(msg)
        return v.lower()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_schemas/test_generate.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/schemas/generate.py projects/qr-code-generator/tests/test_schemas/test_generate.py
git commit -m "feat(qr-code-generator): add request schema with validation"
```

---

### Task 4: QR generation service (TDD)

**Files:**
- Test: `projects/qr-code-generator/tests/test_services/test_generator.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/services/generator.py`

- [ ] **Step 1: Write service tests**

```python
import io

from PIL import Image


class TestGenerateQR:
    def test_png_output_is_valid_png(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com")
        result = generate_qr(params)

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_svg_output_contains_svg_tag(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com", format="svg")
        result = generate_qr(params)

        svg_text = result.decode("utf-8")
        assert "<svg" in svg_text
        assert "</svg>" in svg_text

    def test_custom_colors(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(
            data="test",
            foreground_color="#ff0000",
            background_color="#00ff00",
        )
        result = generate_qr(params)

        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_size_approximates_target(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="test", size=500)
        result = generate_qr(params)

        img = Image.open(io.BytesIO(result))
        assert abs(img.width - 500) < 50

    def test_border_zero(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params_no_border = QRCodeRequest(data="test", border=0)
        params_with_border = QRCodeRequest(data="test", border=4)

        img_no = Image.open(io.BytesIO(generate_qr(params_no_border)))
        img_with = Image.open(io.BytesIO(generate_qr(params_with_border)))
        assert img_no.width < img_with.width

    def test_data_overflow_raises_invalid_data(self) -> None:
        import pytest

        from qr_code_generator.exceptions import InvalidDataError
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="x" * 2953, error_correction="H")
        with pytest.raises(InvalidDataError):
            generate_qr(params)


class TestLogoCompositing:
    def _make_logo(self, width: int = 20, height: int = 20) -> bytes:
        img = Image.new("RGBA", (width, height), (255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_logo_produces_valid_png(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com")
        logo_bytes = self._make_logo()
        result = generate_qr(params, logo_bytes=logo_bytes)

        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_logo_changes_center_pixels(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com", size=300)
        result_no_logo = generate_qr(params)
        result_with_logo = generate_qr(params, logo_bytes=self._make_logo())

        img_no = Image.open(io.BytesIO(result_no_logo)).convert("RGBA")
        img_with = Image.open(io.BytesIO(result_with_logo)).convert("RGBA")
        cx, cy = img_no.width // 2, img_no.height // 2
        assert img_no.getpixel((cx, cy)) != img_with.getpixel((cx, cy))

    def test_error_correction_elevated_to_h_with_logo(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params_l = QRCodeRequest(data="test", error_correction="L")
        params_h = QRCodeRequest(data="test", error_correction="H")

        result_l_logo = generate_qr(params_l, logo_bytes=self._make_logo())
        result_h_no_logo = generate_qr(params_h)

        img_l = Image.open(io.BytesIO(result_l_logo))
        img_h = Image.open(io.BytesIO(result_h_no_logo))
        assert img_l.width == img_h.width

    def test_logo_with_jpeg(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        img = Image.new("RGB", (20, 20), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

        params = QRCodeRequest(data="test")
        result = generate_qr(params, logo_bytes=jpeg_bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"


class TestScaleCalculation:
    def test_small_data_small_target(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="A", size=50, border=0)
        result = generate_qr(params)
        img = Image.open(io.BytesIO(result))
        assert img.width >= 21

    def test_large_target(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="A", size=2000, border=0)
        result = generate_qr(params)
        img = Image.open(io.BytesIO(result))
        assert img.width <= 2000
        assert img.width > 1900
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_services/test_generator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'qr_code_generator.services.generator'`

- [ ] **Step 3: Implement generator service**

```python
import io

import segno
from PIL import Image

from qr_code_generator.exceptions import InvalidDataError
from qr_code_generator.schemas.generate import QRCodeRequest


def _compute_scale(qr: segno.QRCode, target_size: int, border: int) -> int:
    """Calculate scale factor to approximate the target output dimension."""
    total_modules = qr.symbol_size()[0] + 2 * border
    return max(1, target_size // total_modules)


def _composite_logo(qr_png: bytes, logo_bytes: bytes, ratio: float) -> bytes:
    """Paste a logo image centered on the QR code PNG."""
    qr_img = Image.open(io.BytesIO(qr_png)).convert("RGBA")
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

    logo_max_size = int(qr_img.width * ratio)
    logo.thumbnail((logo_max_size, logo_max_size), Image.LANCZOS)

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
        raise InvalidDataError(
            f"data too long for error correction level {error_level}"
        ) from None

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_services/test_generator.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/services/generator.py projects/qr-code-generator/tests/test_services/test_generator.py
git commit -m "feat(qr-code-generator): add QR generation service with logo compositing"
```

---

### Task 5: App factory, middleware, and test infrastructure

**Files:**
- Create: `projects/qr-code-generator/src/qr_code_generator/middleware/cookie_auth.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/main.py`
- Create: `projects/qr-code-generator/tests/conftest.py`

- [ ] **Step 1: Create cookie_auth.py**

Copy from `projects/pdf-from-html/src/pdf_from_html/middleware/cookie_auth.py` verbatim — it has no project-specific imports:

```python
from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_LOGIN_PATH = "/ui/login"
_UI_PREFIX = "/ui/"


class CookieToHeaderMiddleware:
    """Read a signed 'api_key' cookie and inject it as an x-api-key header.

    For UI paths (except the login page), redirect to login when no valid
    cookie is present.  API clients that already send the header are
    unaffected — the cookie is never used when the header exists.
    """

    def __init__(self, app: ASGIApp, secret_key: str) -> None:
        self.app = app
        self.signer = URLSafeSerializer(secret_key, salt="api-key")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        has_header = "x-api-key" in request.headers

        if has_header:
            await self.app(scope, receive, send)
            return

        cookie_value = request.cookies.get("api_key")
        api_key: str | None = None

        if cookie_value:
            try:
                api_key = self.signer.loads(cookie_value)
            except BadSignature:
                api_key = None

        if api_key:
            scope["headers"] = [*scope["headers"], (b"x-api-key", api_key.encode())]
            await self.app(scope, receive, send)
            return

        # No valid credential — redirect to login for UI paths
        if path.startswith(_UI_PREFIX) and path != _LOGIN_PATH:
            response = RedirectResponse(_LOGIN_PATH)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
```

- [ ] **Step 2: Create main.py**

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)

from qr_code_generator.config import get_settings
from qr_code_generator.exceptions import AppError, app_exception_handler
from qr_code_generator.middleware.cookie_auth import CookieToHeaderMiddleware

_STATIC_DIR = Path(__file__).resolve().parent / "static"

_AUTH_SKIP_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/webhooks/stripe",
        "/ui/login",
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
        title="QR Code Generator API",
        description=(
            "Generate QR codes with optional logo embedding. "
            "Supports PNG and SVG output with full customization."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]

    # Middleware stack (last added = outermost = runs first on request)
    app.add_middleware(
        MeteringMiddleware,
        api_name="qr-code-generator",
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

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 3: Create conftest.py**

```python
from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from shared.auth.key_utils import generate_api_key
from shared.auth.models import ApiKey, User
from shared.database import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set env vars required by SharedSettings."""
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("APP_REDIS_URL", "redis://localhost")
    monkeypatch.setenv("APP_COOKIE_SECRET_KEY", "test-cookie-secret")


@pytest.fixture
async def app():  # type: ignore[no-untyped-def]
    """Create app with test doubles for DB and Redis."""
    from qr_code_generator.config import get_settings

    get_settings.cache_clear()

    from qr_code_generator.main import create_app

    application = create_app()

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    application.state.db_engine = engine
    application.state.db_session_factory = session_factory
    application.state.redis = fake_redis
    application.state.shared_settings = get_settings()

    async with session_factory() as session:
        user = User(email="test@test.com")
        session.add(user)
        await session.flush()

        full_key, prefix, key_hash = generate_api_key()
        api_key = ApiKey(key_prefix=prefix, key_hash=key_hash, user_id=user.id, plan="basic")
        session.add(api_key)
        await session.commit()

    application.state._test_api_key = full_key  # noqa: SLF001
    yield application

    await fake_redis.aclose()
    await engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[no-untyped-def]
    """HTTP client that automatically includes the test API key header."""
    api_key = app.state._test_api_key  # noqa: SLF001
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": api_key},
    ) as ac:
        yield ac
```

- [ ] **Step 4: Write health endpoint test**

Create `projects/qr-code-generator/tests/test_health.py`:

```python
from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 5: Run health test**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/middleware/ projects/qr-code-generator/src/qr_code_generator/main.py projects/qr-code-generator/tests/conftest.py projects/qr-code-generator/tests/test_health.py
git commit -m "feat(qr-code-generator): add app factory, middleware, and test infrastructure"
```

---

### Task 6: API route (TDD)

**Files:**
- Test: `projects/qr-code-generator/tests/test_routes/test_generate.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/routes/generate.py`
- Modify: `projects/qr-code-generator/src/qr_code_generator/main.py` (add router include)

- [ ] **Step 1: Write route tests**

```python
import io

from httpx import AsyncClient
from PIL import Image


class TestGenerateQRCodeHappyPath:
    async def test_minimal_request_returns_png(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "https://example.com"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_svg_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "https://example.com", "format": "svg"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml; charset=utf-8"
        assert b"<svg" in response.content

    async def test_custom_colors(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={
                "data": "test",
                "foreground_color": "#FF5733",
                "background_color": "#00FF00",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_custom_size(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "500"},
        )
        assert response.status_code == 200
        img = Image.open(io.BytesIO(response.content))
        assert abs(img.width - 500) < 50

    async def test_content_disposition_header(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
        )
        assert response.headers["content-disposition"] == "inline; filename=qrcode.png"

    async def test_svg_content_disposition(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "format": "svg"},
        )
        assert response.headers["content-disposition"] == "inline; filename=qrcode.svg"


class TestGenerateQRCodeWithLogo:
    def _make_logo_png(self, size: int = 20) -> bytes:
        img = Image.new("RGBA", (size, size), (255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def test_logo_upload_returns_png(self, client: AsyncClient) -> None:
        logo = self._make_logo_png()
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "https://example.com"},
            files={"logo": ("logo.png", logo, "image/png")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_logo_with_svg_returns_422(self, client: AsyncClient) -> None:
        logo = self._make_logo_png()
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "format": "svg"},
            files={"logo": ("logo.png", logo, "image/png")},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "LOGO_SVG_CONFLICT"

    async def test_logo_too_large(self, client: AsyncClient) -> None:
        large_logo = self._make_logo_png(size=1000)
        assert len(large_logo) < 512_000
        oversized = b"\x00" * 512_001
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
            files={"logo": ("logo.png", oversized, "image/png")},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "LOGO_TOO_LARGE"

    async def test_logo_bad_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
            files={"logo": ("logo.gif", b"GIF89a", "image/gif")},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "LOGO_FORMAT_UNSUPPORTED"

    async def test_logo_jpeg_accepted(self, client: AsyncClient) -> None:
        img = Image.new("RGB", (20, 20), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
            files={"logo": ("logo.jpg", buf.getvalue(), "image/jpeg")},
        )
        assert response.status_code == 200


class TestGenerateQRCodeValidation:
    async def test_missing_data(self, client: AsyncClient) -> None:
        response = await client.post("/v1/generate/qrcode", data={})
        assert response.status_code == 422

    async def test_invalid_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "format": "pdf"},
        )
        assert response.status_code == 422

    async def test_invalid_color(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "foreground_color": "notacolor"},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "INVALID_COLOR"

    async def test_size_below_min(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "10"},
        )
        assert response.status_code == 422

    async def test_size_above_max(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "3000"},
        )
        assert response.status_code == 422

    async def test_border_above_max(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "border": "11"},
        )
        assert response.status_code == 422

    async def test_min_boundary_size(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "50"},
        )
        assert response.status_code == 200

    async def test_max_boundary_size(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "2000"},
        )
        assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_routes/test_generate.py -v
```

Expected: FAIL — 404 (route not registered).

- [ ] **Step 3: Implement route**

```python
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
```

- [ ] **Step 4: Wire router into main.py**

Add to `main.py` imports:

```python
from qr_code_generator.routes.generate import router as generate_router
```

Add inside `create_app()`, after `app.mount(...)`:

```python
    app.include_router(generate_router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_routes/test_generate.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Run full test suite**

```bash
cd projects/qr-code-generator && uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/routes/generate.py projects/qr-code-generator/src/qr_code_generator/main.py projects/qr-code-generator/tests/test_routes/test_generate.py
git commit -m "feat(qr-code-generator): add QR code generation API route"
```

---

### Task 7: Caching layer (TDD)

**Files:**
- Test: `projects/qr-code-generator/tests/test_services/test_caching.py`
- Modify: `projects/qr-code-generator/src/qr_code_generator/services/generator.py`
- Modify: `projects/qr-code-generator/src/qr_code_generator/routes/generate.py`

- [ ] **Step 1: Write caching tests**

```python
import fakeredis.aioredis

from qr_code_generator.schemas.generate import QRCodeRequest


class TestCaching:
    async def test_cache_miss_stores_result(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="cache-test")

        result = await generate_qr_cached(params, None, redis, cache_ttl=3600)

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        keys = await redis.keys("qr:*")
        assert len(keys) == 1
        await redis.aclose()

    async def test_cache_hit_returns_cached(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="cache-test-2")

        first = await generate_qr_cached(params, None, redis, cache_ttl=3600)
        second = await generate_qr_cached(params, None, redis, cache_ttl=3600)

        assert first == second
        await redis.aclose()

    async def test_different_params_different_cache_keys(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

        params_a = QRCodeRequest(data="aaa")
        params_b = QRCodeRequest(data="bbb")

        await generate_qr_cached(params_a, None, redis, cache_ttl=3600)
        await generate_qr_cached(params_b, None, redis, cache_ttl=3600)

        keys = await redis.keys("qr:*")
        assert len(keys) == 2
        await redis.aclose()

    async def test_logo_included_in_cache_key(self) -> None:
        import io

        from PIL import Image

        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="logo-cache-test")

        logo_a = io.BytesIO()
        Image.new("RGBA", (10, 10), (255, 0, 0, 255)).save(logo_a, format="PNG")

        logo_b = io.BytesIO()
        Image.new("RGBA", (10, 10), (0, 255, 0, 255)).save(logo_b, format="PNG")

        await generate_qr_cached(params, logo_a.getvalue(), redis, cache_ttl=3600)
        await generate_qr_cached(params, logo_b.getvalue(), redis, cache_ttl=3600)

        keys = await redis.keys("qr:*")
        assert len(keys) == 2
        await redis.aclose()

    async def test_cache_ttl_set(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="ttl-test")

        await generate_qr_cached(params, None, redis, cache_ttl=120)

        keys = await redis.keys("qr:*")
        ttl = await redis.ttl(keys[0])
        assert 0 < ttl <= 120
        await redis.aclose()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_services/test_caching.py -v
```

Expected: FAIL — `ImportError: cannot import name 'generate_qr_cached'`

- [ ] **Step 3: Add caching to generator service**

Add these imports and functions to `services/generator.py`:

```python
import base64
import hashlib
import json

from redis.asyncio import Redis
```

Add after the `generate_qr` function:

```python
def _cache_key(params: QRCodeRequest, logo_bytes: bytes | None) -> str:
    """Compute deterministic cache key from all input parameters."""
    payload = json.dumps(params.model_dump(mode="json"), sort_keys=True)
    if logo_bytes:
        payload += hashlib.sha256(logo_bytes).hexdigest()
    return f"qr:{hashlib.sha256(payload.encode()).hexdigest()}"


async def generate_qr_cached(
    params: QRCodeRequest,
    logo_bytes: bytes | None,
    redis: Redis,  # type: ignore[type-arg]
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
```

- [ ] **Step 4: Update route to use cached generation**

In `routes/generate.py`, change the import:

```python
from qr_code_generator.services.generator import generate_qr_cached
```

Replace the generation call in `generate_qrcode`:

```python
    redis = request.app.state.redis
    content = await generate_qr_cached(params, logo_bytes, redis, settings.cache_ttl)
```

Add `Request` usage — update the function signature to include `request: Request`:

```python
@router.post("/qrcode")
async def generate_qrcode(
    request: Request,
    settings: SettingsDep,
    data: Annotated[str, Form(min_length=1, max_length=2953)],
    ...
```

- [ ] **Step 5: Run all tests**

```bash
cd projects/qr-code-generator && uv run pytest -v
```

Expected: all tests PASS (caching tests + all previous tests).

- [ ] **Step 6: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/services/generator.py projects/qr-code-generator/src/qr_code_generator/routes/generate.py projects/qr-code-generator/tests/test_services/test_caching.py
git commit -m "feat(qr-code-generator): add Redis caching for generated QR codes"
```

---

### Task 8: Web UI — templates and static assets

**Files:**
- Create: `projects/qr-code-generator/src/qr_code_generator/templates/base.html`
- Create: `projects/qr-code-generator/src/qr_code_generator/templates/login.html`
- Create: `projects/qr-code-generator/src/qr_code_generator/templates/generate.html`

- [ ] **Step 1: Create base.html**

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}QR Code Generator{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/pico.min.css">
    <script src="/static/js/htmx.min.js" defer></script>
</head>
<body>
    <header class="container">
        <nav>
            <ul>
                <li><strong>QR Code Generator</strong></li>
            </ul>
            {% if authenticated %}
            <ul>
                <li><a href="/ui/">Generate</a></li>
                <li>
                    <form method="POST" action="/ui/logout" style="margin:0">
                        <button type="submit" class="outline secondary">Logout</button>
                    </form>
                </li>
            </ul>
            {% endif %}
        </nav>
    </header>
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Create login.html**

```html
{% extends "base.html" %}
{% block title %}Login — QR Code Generator{% endblock %}
{% block content %}
<article>
    <header>
        <h2>Enter your API Key</h2>
        <p>Use your API key to access the QR code generator.</p>
    </header>
    {% if error %}
    <p role="alert" style="color: var(--pico-color-red-500);">{{ error }}</p>
    {% endif %}
    <form method="POST" action="/ui/login">
        <label for="api_key">API Key</label>
        <input type="password" id="api_key" name="api_key" required
               placeholder="sk_..." autocomplete="off">
        <button type="submit">Login</button>
    </form>
</article>
{% endblock %}
```

- [ ] **Step 3: Create generate.html**

```html
{% extends "base.html" %}
{% block title %}Generate QR Code{% endblock %}
{% block content %}
<article>
    <header>
        <h2>Generate QR Code</h2>
    </header>
    <form id="qr-form">
        <label for="data">Data / URL</label>
        <input type="text" id="data" name="data" required
               placeholder="https://example.com or any text">

        <div class="grid">
            <label>
                Format
                <select id="format" name="format">
                    <option value="png" selected>PNG</option>
                    <option value="svg">SVG</option>
                </select>
            </label>
            <label>
                Size (px)
                <input type="number" id="size" name="size"
                       value="300" min="50" max="2000" step="50">
            </label>
        </div>

        <details>
            <summary>Advanced Options</summary>
            <div class="grid">
                <label>
                    Error Correction
                    <select id="error_correction" name="error_correction">
                        <option value="L">L (7%)</option>
                        <option value="M" selected>M (15%)</option>
                        <option value="Q">Q (25%)</option>
                        <option value="H">H (30%)</option>
                    </select>
                </label>
                <label>
                    Border (modules)
                    <input type="number" id="border" name="border"
                           value="4" min="0" max="10">
                </label>
            </div>
            <div class="grid">
                <label>
                    Foreground Color
                    <input type="color" id="foreground_color" name="foreground_color"
                           value="#000000">
                </label>
                <label>
                    Background Color
                    <input type="color" id="background_color" name="background_color"
                           value="#FFFFFF">
                </label>
            </div>
        </details>

        <details>
            <summary>Logo (optional)</summary>
            <label for="logo">Upload Logo (PNG, JPEG, or WEBP — max 500 KB)</label>
            <input type="file" id="logo" name="logo"
                   accept="image/png,image/jpeg,image/webp">
            <p id="logo-error" role="alert"
               style="color: var(--pico-color-red-500); display: none;"></p>
            <label>
                Logo Size Ratio
                <input type="range" id="logo_size_ratio" name="logo_size_ratio"
                       min="0.1" max="0.4" step="0.05" value="0.25">
                <small id="ratio-display">25%</small>
            </label>
        </details>

        <div id="error-message" role="alert"
             style="color: var(--pico-color-red-500); display: none;"></div>

        <button type="submit" id="submit-btn">Generate QR Code</button>
    </form>

    <div id="preview-section" style="display: none; text-align: center; margin-top: 2rem;">
        <h3>Preview</h3>
        <img id="preview-img" alt="Generated QR Code" style="max-width: 100%; border: 1px solid var(--pico-muted-border-color); border-radius: 4px;">
        <br>
        <a id="download-link" download="qrcode.png">
            <button type="button" class="outline" style="margin-top: 1rem;">Download</button>
        </a>
    </div>
</article>
{% endblock %}

{% block scripts %}
<script>
(function () {
    const form = document.getElementById("qr-form");
    const submitBtn = document.getElementById("submit-btn");
    const errorDiv = document.getElementById("error-message");
    const previewSection = document.getElementById("preview-section");
    const previewImg = document.getElementById("preview-img");
    const downloadLink = document.getElementById("download-link");
    const logoInput = document.getElementById("logo");
    const logoError = document.getElementById("logo-error");
    const ratioInput = document.getElementById("logo_size_ratio");
    const ratioDisplay = document.getElementById("ratio-display");

    var currentObjectUrl = null;

    ratioInput.addEventListener("input", function () {
        ratioDisplay.textContent = Math.round(this.value * 100) + "%";
    });

    logoInput.addEventListener("change", function () {
        logoError.style.display = "none";
        var file = this.files[0];
        if (!file) return;

        var maxSize = 500 * 1024;
        if (file.size > maxSize) {
            logoError.textContent = "Logo file exceeds 500 KB limit.";
            logoError.style.display = "block";
            this.value = "";
            return;
        }

        var allowed = ["image/png", "image/jpeg", "image/webp"];
        if (allowed.indexOf(file.type) === -1) {
            logoError.textContent = "Only PNG, JPEG, and WEBP files are accepted.";
            logoError.style.display = "block";
            this.value = "";
            return;
        }
    });

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        errorDiv.style.display = "none";
        previewSection.style.display = "none";
        submitBtn.disabled = true;
        submitBtn.setAttribute("aria-busy", "true");
        submitBtn.textContent = "Generating\u2026";

        var formData = new FormData();
        formData.append("data", document.getElementById("data").value);
        formData.append("format", document.getElementById("format").value);
        formData.append("size", document.getElementById("size").value);
        formData.append("error_correction", document.getElementById("error_correction").value);
        formData.append("border", document.getElementById("border").value);
        formData.append("foreground_color", document.getElementById("foreground_color").value);
        formData.append("background_color", document.getElementById("background_color").value);
        formData.append("logo_size_ratio", document.getElementById("logo_size_ratio").value);

        var logoFile = logoInput.files[0];
        if (logoFile) {
            formData.append("logo", logoFile);
        }

        try {
            var response = await fetch("/v1/generate/qrcode", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                var data = await response.json();
                errorDiv.textContent = data.detail || "Failed to generate QR code";
                errorDiv.style.display = "block";
                return;
            }

            if (currentObjectUrl) {
                URL.revokeObjectURL(currentObjectUrl);
            }

            var blob = await response.blob();
            currentObjectUrl = URL.createObjectURL(blob);
            previewImg.src = currentObjectUrl;

            var fmt = document.getElementById("format").value;
            downloadLink.href = currentObjectUrl;
            downloadLink.download = "qrcode." + fmt;
            previewSection.style.display = "block";
        } catch (err) {
            errorDiv.textContent = "Network error \u2014 please try again.";
            errorDiv.style.display = "block";
        } finally {
            submitBtn.disabled = false;
            submitBtn.removeAttribute("aria-busy");
            submitBtn.textContent = "Generate QR Code";
        }
    });
})();
</script>
{% endblock %}
```

- [ ] **Step 4: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/templates/
git commit -m "feat(qr-code-generator): add web UI templates with client-side logo validation"
```

---

### Task 9: UI routes (TDD)

**Files:**
- Test: `projects/qr-code-generator/tests/test_routes/test_ui.py`
- Create: `projects/qr-code-generator/src/qr_code_generator/routes/ui.py`
- Modify: `projects/qr-code-generator/src/qr_code_generator/main.py` (add UI router)

- [ ] **Step 1: Write UI route tests**

```python
from httpx import AsyncClient


class TestLoginPage:
    async def test_login_page_renders(self, client: AsyncClient) -> None:
        response = await client.get("/ui/login")
        assert response.status_code == 200
        assert "Enter your API Key" in response.text

    async def test_login_with_valid_key(self, client: AsyncClient, app) -> None:  # type: ignore[no-untyped-def]
        api_key = app.state._test_api_key  # noqa: SLF001
        response = await client.post(
            "/ui/login",
            data={"api_key": api_key},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/"
        assert "api_key" in response.headers.get("set-cookie", "")

    async def test_login_with_invalid_key(self, client: AsyncClient) -> None:
        response = await client.post(
            "/ui/login",
            data={"api_key": "sk_invalid_key"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Invalid API key" in response.text


class TestLogout:
    async def test_logout_redirects(self, client: AsyncClient) -> None:
        response = await client.post("/ui/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/login"


class TestGeneratePage:
    async def test_generate_page_renders(self, client: AsyncClient) -> None:
        response = await client.get("/ui/")
        assert response.status_code == 200
        assert "Generate QR Code" in response.text
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/qr-code-generator && uv run pytest tests/test_routes/test_ui.py -v
```

Expected: FAIL — 404 or missing routes.

- [ ] **Step 3: Implement UI routes**

```python
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer
from shared.auth.api_key import validate_api_key_direct

from qr_code_generator.config import Settings, get_settings

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(prefix="/ui", tags=["ui"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _get_signer(settings: Settings) -> URLSafeSerializer:
    return URLSafeSerializer(settings.cookie_secret_key, salt="api-key")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"authenticated": False})


@router.post("/login", response_model=None)
async def login_submit(
    request: Request,
    settings: SettingsDep,
    api_key: Annotated[str, Form()],
) -> Response:
    redis = request.app.state.redis
    session_factory = request.app.state.db_session_factory

    try:
        async with session_factory() as session:
            await validate_api_key_direct(api_key, redis, session)
    except Exception:
        return templates.TemplateResponse(
            request, "login.html", {"authenticated": False, "error": "Invalid API key."}
        )

    signer = _get_signer(settings)
    signed_key = signer.dumps(api_key)
    response = RedirectResponse("/ui/", status_code=303)
    response.set_cookie(
        "api_key",
        signed_key,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse("/ui/login", status_code=303)
    response.delete_cookie("api_key")
    return response


@router.get("/", response_class=HTMLResponse)
async def generate_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "generate.html", {"authenticated": True})
```

- [ ] **Step 4: Wire UI router into main.py**

Add import:

```python
from qr_code_generator.routes.ui import router as ui_router
```

Add inside `create_app()`, after the generate router:

```python
    app.include_router(ui_router)
```

- [ ] **Step 5: Run all tests**

```bash
cd projects/qr-code-generator && uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 6: Lint and type check**

```bash
cd projects/qr-code-generator && uv run ruff check . --fix && uv run ruff format .
```

- [ ] **Step 7: Commit**

```bash
git add projects/qr-code-generator/src/qr_code_generator/routes/ui.py projects/qr-code-generator/src/qr_code_generator/main.py projects/qr-code-generator/tests/test_routes/test_ui.py
git commit -m "feat(qr-code-generator): add web UI routes with login and generate pages"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run full test suite with coverage**

```bash
cd projects/qr-code-generator && uv run pytest --cov=src/qr_code_generator --cov-report=term-missing -v
```

Expected: all tests PASS, reasonable coverage.

- [ ] **Step 2: Lint**

```bash
cd projects/qr-code-generator && uv run ruff check . && uv run ruff format --check .
```

Expected: clean.

- [ ] **Step 3: Start dev server and test manually**

```bash
cd projects/qr-code-generator && uv run fastapi dev src/qr_code_generator/main.py
```

Open `http://127.0.0.1:8000/docs` — verify OpenAPI docs show the `/v1/generate/qrcode` endpoint.

Open `http://127.0.0.1:8000/health` — verify `{"status": "ok"}`.

- [ ] **Step 4: Commit any remaining fixes**

```bash
cd projects/qr-code-generator && git add -A && git commit -m "chore(qr-code-generator): final cleanup and verification"
```
