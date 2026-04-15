# PDF from HTML — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status note (2026-04-15):** This plan reflects the original
> Playwright/Chromium build plan. The current implementation in
> `projects/pdf-from-html/` ships with `xhtml2pdf` instead. Treat this file as
> historical implementation planning, not current source-of-truth behavior.

**Goal:** Build a production-grade API that converts raw HTML or URLs into PDFs using Playwright/Chromium, integrated with shared auth/billing/metering infrastructure.

**Architecture:** Original plan: single POST endpoint accepts `source` ("raw"/"url") + `content` + optional PDF options. Playwright renders via a pooled browser, returns PDF bytes as StreamingResponse. Current implementation differs and uses `xhtml2pdf` without a browser pool.

**Tech Stack:** Planned stack: FastAPI, Playwright (Chromium), Pydantic v2, asyncio, shared infrastructure (auth, billing, metering, Redis, PostgreSQL). Current shipped renderer: `xhtml2pdf`.

**Spec:** `docs/superpowers/specs/2026-04-13-pdf-from-html-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `projects/pdf-from-html/pyproject.toml` | Dependencies, tool config |
| `src/pdf_from_html/__init__.py` | Package marker |
| `src/pdf_from_html/main.py` | App factory, lifespan (browser + shared), middleware stack |
| `src/pdf_from_html/config.py` | Settings extending SharedSettings |
| `src/pdf_from_html/exceptions.py` | AppError subclasses + global handler |
| `src/pdf_from_html/schemas/__init__.py` | Package marker |
| `src/pdf_from_html/schemas/generate.py` | Margin, PDFOptions, PDFGenerateRequest |
| `src/pdf_from_html/routes/__init__.py` | Package marker |
| `src/pdf_from_html/routes/generate.py` | POST /v1/generate/pdf endpoint |
| `src/pdf_from_html/services/__init__.py` | Package marker |
| `src/pdf_from_html/services/browser_pool.py` | Planned BrowserPool for Playwright version; not present in current implementation |
| `src/pdf_from_html/services/pdf_service.py` | PDF generation service |
| `src/pdf_from_html/dependencies/__init__.py` | Package marker |
| `tests/conftest.py` | App fixture and test client |
| `tests/test_routes/test_generate.py` | Route-level tests (mock service layer) |
| `tests/test_services/test_pdf_service.py` | Service + options-builder tests |
| `tests/test_services/test_browser_pool.py` | Pool lifecycle tests |

---

### Task 1: Project Scaffold

**Files:**
- Create: `projects/pdf-from-html/pyproject.toml`
- Create: `projects/pdf-from-html/src/pdf_from_html/__init__.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/schemas/__init__.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/routes/__init__.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/services/__init__.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/dependencies/__init__.py`
- Create: `projects/pdf-from-html/tests/__init__.py`
- Create: `projects/pdf-from-html/tests/test_routes/__init__.py`
- Create: `projects/pdf-from-html/tests/test_services/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pdf-from-html"
version = "0.1.0"
description = "PDF from HTML API — generate PDFs from raw HTML or URLs using xhtml2pdf"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.7.0",
    "playwright>=1.52.0",
    "shared",
]

[tool.hatch.build.targets.wheel]
packages = ["src/pdf_from_html"]

[tool.hatch.metadata]
allow-direct-references = true

[tool.uv.sources]
shared = { path = "../../shared", editable = true }

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
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

- [ ] **Step 2: Create all `__init__.py` files**

Create empty files at every path listed in the Files section above.

- [ ] **Step 3: Install dependencies and Playwright browsers**

Run from `projects/pdf-from-html/`:

```bash
cd projects/pdf-from-html && uv sync
uv run playwright install chromium
```

Expected: dependencies resolve, Chromium binary downloads.

- [ ] **Step 4: Commit**

```bash
git add projects/pdf-from-html/
git commit -m "chore(pdf-from-html): scaffold project structure and dependencies"
```

---

### Task 2: Configuration and Exceptions

**Files:**
- Create: `projects/pdf-from-html/src/pdf_from_html/config.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/exceptions.py`

- [ ] **Step 1: Write config.py**

```python
from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    browser_pool_size: int = 3
    render_timeout: float = 30.0
    max_content_size: int = 5_242_880
    default_format: str = "A4"
    default_orientation: str = "portrait"
    default_margin_top: str = "20mm"
    default_margin_right: str = "20mm"
    default_margin_bottom: str = "20mm"
    default_margin_left: str = "20mm"
    default_scale: float = 1.0
    default_print_background: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Write exceptions.py**

```python
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


class BrowserPoolExhaustedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=503,
            detail="All browser instances are busy — try again shortly",
            error_code="POOL_EXHAUSTED",
        )


async def app_exception_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.detail},
    )
```

- [ ] **Step 3: Verify imports work**

```bash
cd projects/pdf-from-html && uv run python -c "from pdf_from_html.config import get_settings; from pdf_from_html.exceptions import AppError; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/config.py projects/pdf-from-html/src/pdf_from_html/exceptions.py
git commit -m "feat(pdf-from-html): add configuration and exception classes"
```

---

### Task 3: Pydantic Schemas (TDD)

**Files:**
- Create: `projects/pdf-from-html/src/pdf_from_html/schemas/generate.py`
- Create: `projects/pdf-from-html/tests/test_schemas/__init__.py`
- Create: `projects/pdf-from-html/tests/test_schemas/test_generate.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_schemas/__init__.py` (empty) and `tests/test_schemas/test_generate.py`:

```python
import pytest
from pydantic import ValidationError


class TestMargin:
    def test_defaults(self) -> None:
        from pdf_from_html.schemas.generate import Margin

        m = Margin()
        assert m.top == "20mm"
        assert m.right == "20mm"
        assert m.bottom == "20mm"
        assert m.left == "20mm"


class TestPDFOptions:
    def test_defaults(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions

        opts = PDFOptions()
        assert opts.format == "A4"
        assert opts.orientation == "portrait"
        assert opts.scale == 1.0
        assert opts.print_background is True
        assert opts.page_ranges is None
        assert opts.header_html is None
        assert opts.footer_html is None
        assert opts.width is None
        assert opts.height is None

    def test_invalid_format_rejected(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions

        with pytest.raises(ValidationError):
            PDFOptions(format="B5")

    def test_invalid_orientation_rejected(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions

        with pytest.raises(ValidationError):
            PDFOptions(orientation="diagonal")

    def test_scale_below_minimum_rejected(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions

        with pytest.raises(ValidationError, match="Scale must be between"):
            PDFOptions(scale=0.05)

    def test_scale_above_maximum_rejected(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions

        with pytest.raises(ValidationError, match="Scale must be between"):
            PDFOptions(scale=3.0)

    def test_valid_scale_accepted(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions

        opts = PDFOptions(scale=0.5)
        assert opts.scale == 0.5


class TestPDFGenerateRequest:
    def test_raw_source_valid(self) -> None:
        from pdf_from_html.schemas.generate import PDFGenerateRequest

        req = PDFGenerateRequest(source="raw", content="<html>Hello</html>")
        assert req.source == "raw"
        assert req.content == "<html>Hello</html>"

    def test_url_source_valid(self) -> None:
        from pdf_from_html.schemas.generate import PDFGenerateRequest

        req = PDFGenerateRequest(source="url", content="https://example.com")
        assert req.source == "url"

    def test_invalid_source_rejected(self) -> None:
        from pdf_from_html.schemas.generate import PDFGenerateRequest

        with pytest.raises(ValidationError):
            PDFGenerateRequest(source="file", content="test")

    def test_empty_content_rejected(self) -> None:
        from pdf_from_html.schemas.generate import PDFGenerateRequest

        with pytest.raises(ValidationError):
            PDFGenerateRequest(source="raw", content="")

    def test_options_default_applied(self) -> None:
        from pdf_from_html.schemas.generate import PDFGenerateRequest

        req = PDFGenerateRequest(source="raw", content="<html>test</html>")
        assert req.options.format == "A4"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_schemas/test_generate.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pdf_from_html.schemas.generate'`

- [ ] **Step 3: Implement schemas**

Create `src/pdf_from_html/schemas/generate.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Margin(BaseModel):
    top: str = "20mm"
    right: str = "20mm"
    bottom: str = "20mm"
    left: str = "20mm"


class PDFOptions(BaseModel):
    format: Literal["A4", "Letter", "Legal", "Tabloid"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: Margin = Field(default_factory=Margin)
    scale: float = 1.0
    print_background: bool = True
    page_ranges: str | None = None
    header_html: str | None = None
    footer_html: str | None = None
    width: str | None = None
    height: str | None = None

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, v: float) -> float:
        if not 0.1 <= v <= 2.0:
            msg = "Scale must be between 0.1 and 2.0"
            raise ValueError(msg)
        return v


class PDFGenerateRequest(BaseModel):
    source: Literal["raw", "url"]
    content: str = Field(min_length=1)
    options: PDFOptions = Field(default_factory=PDFOptions)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_schemas/test_generate.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/schemas/generate.py projects/pdf-from-html/tests/test_schemas/
git commit -m "feat(pdf-from-html): add Pydantic schemas for PDF generation request"
```

---

### Task 4: BrowserPool (TDD)

**Files:**
- Create: `projects/pdf-from-html/src/pdf_from_html/services/browser_pool.py`
- Create: `projects/pdf-from-html/tests/test_services/test_browser_pool.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_services/test_browser_pool.py`:

```python
from unittest.mock import AsyncMock, MagicMock

import pytest


def _mock_browser() -> MagicMock:
    """Create a mock Playwright Browser that produces mock contexts and pages."""
    browser = MagicMock()
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    browser.new_context = AsyncMock(return_value=mock_context)
    browser.close = AsyncMock()
    return browser


class TestBrowserPool:
    async def test_acquire_yields_page(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=2)
        async with pool.acquire() as page:
            assert page is not None
        browser.new_context.assert_awaited_once()

    async def test_page_and_context_closed_after_release(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=2)
        async with pool.acquire() as page:
            context = browser.new_context.return_value
        page.close.assert_awaited_once()
        context.close.assert_awaited_once()

    async def test_pool_exhaustion_raises_error(self) -> None:
        from pdf_from_html.exceptions import BrowserPoolExhaustedError
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=1)

        async with pool.acquire():
            with pytest.raises(BrowserPoolExhaustedError):
                async with pool.acquire():
                    pass

    async def test_semaphore_released_after_use(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=1)

        async with pool.acquire():
            pass

        # Should succeed — semaphore was released
        async with pool.acquire():
            pass

    async def test_semaphore_released_on_exception(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=1)

        with pytest.raises(RuntimeError):
            async with pool.acquire():
                raise RuntimeError("boom")

        # Should succeed — semaphore was released despite exception
        async with pool.acquire():
            pass

    async def test_close_closes_browser(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=2)
        await pool.close()
        browser.close.assert_awaited_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_services/test_browser_pool.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pdf_from_html.services.browser_pool'`

- [ ] **Step 3: Implement BrowserPool**

Create `src/pdf_from_html/services/browser_pool.py`:

```python
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page

from pdf_from_html.exceptions import BrowserPoolExhaustedError

_ACQUIRE_TIMEOUT = 5.0


class BrowserPool:
    """Manages a pool of Playwright browser contexts with bounded concurrency."""

    def __init__(self, browser: Browser, pool_size: int) -> None:
        self._browser = browser
        self._semaphore = asyncio.Semaphore(pool_size)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Page]:
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=_ACQUIRE_TIMEOUT)
        except TimeoutError:
            raise BrowserPoolExhaustedError()

        try:
            context = await self._browser.new_context()
            page = await context.new_page()
        except Exception:
            self._semaphore.release()
            raise

        try:
            yield page
        finally:
            await page.close()
            await context.close()
            self._semaphore.release()

    async def close(self) -> None:
        await self._browser.close()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_services/test_browser_pool.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/services/browser_pool.py projects/pdf-from-html/tests/test_services/test_browser_pool.py
git commit -m "feat(pdf-from-html): add BrowserPool with semaphore-based concurrency"
```

---

### Task 5: PDF Service (TDD)

**Files:**
- Create: `projects/pdf-from-html/src/pdf_from_html/services/pdf_service.py`
- Create: `projects/pdf-from-html/tests/test_services/test_pdf_service.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_services/test_pdf_service.py`:

```python
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_pool_and_page() -> tuple[MagicMock, AsyncMock]:
    """Create a mock BrowserPool that yields a mock Page."""
    pool = MagicMock()
    mock_page = AsyncMock()
    mock_page.pdf = AsyncMock(return_value=b"%PDF-1.4 test")
    mock_page.set_content = AsyncMock()
    mock_page.goto = AsyncMock()

    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_page)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acquire_cm

    return pool, mock_page


class TestBuildPDFOptions:
    def test_defaults(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_pdf_options

        result = _build_pdf_options(PDFOptions())
        assert result["format"] == "A4"
        assert result["landscape"] is False
        assert result["scale"] == 1.0
        assert result["print_background"] is True
        assert result["margin"] == {
            "top": "20mm",
            "right": "20mm",
            "bottom": "20mm",
            "left": "20mm",
        }
        assert "page_ranges" not in result
        assert "display_header_footer" not in result
        assert "width" not in result
        assert "height" not in result

    def test_landscape_orientation(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_pdf_options

        result = _build_pdf_options(PDFOptions(orientation="landscape"))
        assert result["landscape"] is True

    def test_header_and_footer(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_pdf_options

        result = _build_pdf_options(
            PDFOptions(header_html="<div>Header</div>", footer_html="<div>Footer</div>")
        )
        assert result["display_header_footer"] is True
        assert result["header_template"] == "<div>Header</div>"
        assert result["footer_template"] == "<div>Footer</div>"

    def test_header_only(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_pdf_options

        result = _build_pdf_options(PDFOptions(header_html="<div>H</div>"))
        assert result["display_header_footer"] is True
        assert result["header_template"] == "<div>H</div>"
        assert "footer_template" not in result

    def test_custom_dimensions(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_pdf_options

        result = _build_pdf_options(PDFOptions(width="100mm", height="200mm"))
        assert result["width"] == "100mm"
        assert result["height"] == "200mm"

    def test_page_ranges(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_pdf_options

        result = _build_pdf_options(PDFOptions(page_ranges="1-3, 5"))
        assert result["page_ranges"] == "1-3, 5"


class TestGenerate:
    async def test_raw_html_uses_set_content(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        pool, page = _make_pool_and_page()
        result = await generate("raw", "<html>Hi</html>", PDFOptions(), pool, timeout=30.0)
        page.set_content.assert_awaited_once()
        page.goto.assert_not_awaited()
        assert result == b"%PDF-1.4 test"

    async def test_url_uses_goto(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        pool, page = _make_pool_and_page()
        result = await generate("url", "https://example.com", PDFOptions(), pool, timeout=30.0)
        page.goto.assert_awaited_once()
        page.set_content.assert_not_awaited()
        assert result == b"%PDF-1.4 test"

    async def test_timeout_ms_passed_to_playwright(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        pool, page = _make_pool_and_page()
        await generate("raw", "<html>test</html>", PDFOptions(), pool, timeout=15.0)
        call_kwargs = page.set_content.call_args.kwargs
        assert call_kwargs["timeout"] == 15000.0

    async def test_playwright_timeout_raises_render_timeout(self) -> None:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        from pdf_from_html.exceptions import RenderTimeoutError
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        pool, page = _make_pool_and_page()
        page.set_content.side_effect = PlaywrightTimeoutError("Timeout 30000ms exceeded")
        with pytest.raises(RenderTimeoutError):
            await generate("raw", "<html>slow</html>", PDFOptions(), pool, timeout=30.0)

    async def test_playwright_error_raises_render_failed(self) -> None:
        from playwright.async_api import Error as PlaywrightError

        from pdf_from_html.exceptions import RenderFailedError
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        pool, page = _make_pool_and_page()
        page.goto.side_effect = PlaywrightError("net::ERR_NAME_NOT_RESOLVED")
        with pytest.raises(RenderFailedError):
            await generate("url", "https://bad.invalid", PDFOptions(), pool, timeout=30.0)

    async def test_options_forwarded_to_page_pdf(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        pool, page = _make_pool_and_page()
        opts = PDFOptions(format="Letter", orientation="landscape", scale=0.5)
        await generate("raw", "<html>test</html>", opts, pool, timeout=30.0)
        pdf_kwargs = page.pdf.call_args.kwargs
        assert pdf_kwargs["format"] == "Letter"
        assert pdf_kwargs["landscape"] is True
        assert pdf_kwargs["scale"] == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_services/test_pdf_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pdf_from_html.services.pdf_service'`

- [ ] **Step 3: Implement PDF service**

Create `src/pdf_from_html/services/pdf_service.py`:

```python
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from pdf_from_html.exceptions import RenderFailedError, RenderTimeoutError
from pdf_from_html.schemas.generate import PDFOptions
from pdf_from_html.services.browser_pool import BrowserPool


def _build_pdf_options(options: PDFOptions) -> dict[str, object]:
    """Convert PDFOptions into Playwright page.pdf() kwargs."""
    pdf_opts: dict[str, object] = {
        "format": options.format,
        "landscape": options.orientation == "landscape",
        "margin": {
            "top": options.margin.top,
            "right": options.margin.right,
            "bottom": options.margin.bottom,
            "left": options.margin.left,
        },
        "scale": options.scale,
        "print_background": options.print_background,
    }

    if options.page_ranges is not None:
        pdf_opts["page_ranges"] = options.page_ranges

    if options.header_html is not None or options.footer_html is not None:
        pdf_opts["display_header_footer"] = True
        if options.header_html is not None:
            pdf_opts["header_template"] = options.header_html
        if options.footer_html is not None:
            pdf_opts["footer_template"] = options.footer_html

    if options.width is not None:
        pdf_opts["width"] = options.width
    if options.height is not None:
        pdf_opts["height"] = options.height

    return pdf_opts


async def generate(
    source: str,
    content: str,
    options: PDFOptions,
    pool: BrowserPool,
    timeout: float,
) -> bytes:
    """Generate a PDF from HTML content or URL."""
    async with pool.acquire() as page:
        timeout_ms = timeout * 1000
        try:
            if source == "url":
                await page.goto(content, wait_until="networkidle", timeout=timeout_ms)
            else:
                await page.set_content(
                    content, wait_until="networkidle", timeout=timeout_ms
                )

            pdf_options = _build_pdf_options(options)
            return await page.pdf(**pdf_options)
        except PlaywrightTimeoutError:
            raise RenderTimeoutError(timeout) from None
        except PlaywrightError as exc:
            raise RenderFailedError(str(exc)) from None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_services/test_pdf_service.py -v
```

Expected: all 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/services/pdf_service.py projects/pdf-from-html/tests/test_services/test_pdf_service.py
git commit -m "feat(pdf-from-html): add PDF service with Playwright rendering"
```

---

### Task 6: Route, App Factory, and Test Infrastructure (TDD)

**Files:**
- Create: `projects/pdf-from-html/src/pdf_from_html/routes/generate.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/main.py`
- Create: `projects/pdf-from-html/tests/conftest.py`
- Create: `projects/pdf-from-html/tests/test_routes/test_generate.py`

- [ ] **Step 1: Write conftest.py**

Create `tests/conftest.py`:

```python
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

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


@pytest.fixture
def mock_browser_pool() -> MagicMock:
    """A mock BrowserPool whose acquire() yields a mock Page returning fake PDF bytes."""
    pool = MagicMock()
    mock_page = AsyncMock()
    mock_page.pdf = AsyncMock(return_value=b"%PDF-1.4 fake pdf content")
    mock_page.set_content = AsyncMock()
    mock_page.goto = AsyncMock()

    acquire_cm = AsyncMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_page)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acquire_cm
    pool._mock_page = mock_page  # noqa: SLF001

    return pool


@pytest.fixture
async def app(mock_browser_pool: MagicMock):  # type: ignore[no-untyped-def]
    """Create app with test doubles for DB, Redis, and browser pool."""
    from pdf_from_html.config import get_settings

    get_settings.cache_clear()

    from pdf_from_html.main import create_app

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
    application.state.browser_pool = mock_browser_pool

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

- [ ] **Step 2: Write the failing route tests**

Create `tests/test_routes/test_generate.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestGeneratePDF:
    async def test_raw_html_returns_pdf(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 fake content",
        ):
            response = await client.post(
                "/v1/generate/pdf",
                json={"source": "raw", "content": "<html><body>Hello</body></html>"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content == b"%PDF-1.4 fake content"

    async def test_url_source_returns_pdf(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 url content",
        ):
            response = await client.post(
                "/v1/generate/pdf",
                json={"source": "url", "content": "https://example.com"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    async def test_invalid_source_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "file", "content": "test"},
        )
        assert response.status_code == 422

    async def test_empty_content_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "raw", "content": ""},
        )
        assert response.status_code == 422

    async def test_missing_content_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "raw"},
        )
        assert response.status_code == 422

    async def test_url_with_file_scheme_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "url", "content": "file:///etc/passwd"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_URL"

    async def test_url_with_javascript_scheme_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "url", "content": "javascript:alert(1)"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_URL"

    async def test_url_with_data_scheme_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "url", "content": "data:text/html,<h1>hi</h1>"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_URL"

    async def test_content_too_large(self, client: AsyncClient) -> None:
        large_content = "x" * (5 * 1024 * 1024 + 1)
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "raw", "content": large_content},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "CONTENT_TOO_LARGE"

    async def test_custom_options_forwarded(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 fake",
        ) as mock_gen:
            response = await client.post(
                "/v1/generate/pdf",
                json={
                    "source": "raw",
                    "content": "<html>test</html>",
                    "options": {
                        "format": "Letter",
                        "orientation": "landscape",
                        "scale": 0.5,
                    },
                },
            )
        assert response.status_code == 200
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs["options"].format == "Letter"
        assert call_kwargs["options"].orientation == "landscape"
        assert call_kwargs["options"].scale == 0.5

    async def test_default_options_when_omitted(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 fake",
        ) as mock_gen:
            response = await client.post(
                "/v1/generate/pdf",
                json={"source": "raw", "content": "<html>test</html>"},
            )
        assert response.status_code == 200
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs["options"].format == "A4"
        assert call_kwargs["options"].orientation == "portrait"

    async def test_invalid_scale_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={
                "source": "raw",
                "content": "<html>test</html>",
                "options": {"scale": 3.0},
            },
        )
        assert response.status_code == 422


class TestHealthCheck:
    async def test_health(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_routes/test_generate.py -v
```

Expected: FAIL — import errors (main.py and routes/generate.py don't exist yet).

- [ ] **Step 4: Implement route handler**

Create `src/pdf_from_html/routes/generate.py`:

```python
import io
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from pdf_from_html.config import Settings, get_settings
from pdf_from_html.exceptions import ContentTooLargeError, InvalidURLError
from pdf_from_html.schemas.generate import PDFGenerateRequest
from pdf_from_html.services.browser_pool import BrowserPool
from pdf_from_html.services.pdf_service import generate

router = APIRouter(prefix="/v1/generate", tags=["generate"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _validate_url(url: str) -> None:
    """Reject non-HTTP(S) URLs to prevent SSRF."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidURLError(url)


@router.post("/pdf")
async def generate_pdf(
    body: PDFGenerateRequest,
    settings: SettingsDep,
    request: Request,
) -> StreamingResponse:
    """Generate a PDF from raw HTML or a URL."""
    if body.source == "url":
        _validate_url(body.content)
    elif len(body.content.encode("utf-8")) > settings.max_content_size:
        raise ContentTooLargeError(settings.max_content_size)

    pool: BrowserPool = request.app.state.browser_pool
    pdf_bytes = await generate(
        source=body.source,
        content=body.content,
        options=body.options,
        pool=pool,
        timeout=settings.render_timeout,
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="document.pdf"'},
    )
```

- [ ] **Step 5: Implement app factory**

Create `src/pdf_from_html/main.py`:

```python
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
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd projects/pdf-from-html && uv run pytest tests/test_routes/test_generate.py -v
```

Expected: all 13 tests PASS.

- [ ] **Step 7: Run full test suite**

```bash
cd projects/pdf-from-html && uv run pytest -v
```

Expected: all tests across schemas, services, and routes PASS.

- [ ] **Step 8: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/main.py projects/pdf-from-html/src/pdf_from_html/routes/generate.py projects/pdf-from-html/tests/
git commit -m "feat(pdf-from-html): add route handler, app factory, and full test suite"
```

---

### Task 7: Lint, Type Check, and Final Verification

**Files:**
- Modify: any files that fail linting or type checks

- [ ] **Step 1: Run ruff format**

```bash
cd projects/pdf-from-html && uv run ruff format .
```

Expected: files formatted (or already clean).

- [ ] **Step 2: Run ruff lint**

```bash
cd projects/pdf-from-html && uv run ruff check . --fix
```

Expected: no errors (or auto-fixed).

- [ ] **Step 3: Run mypy**

```bash
cd projects/pdf-from-html && uv run mypy src/
```

Expected: `Success: no issues found`. If there are issues, fix them — common ones:
- Add `# type: ignore[arg-type]` for the exception handler registration (same as email-validation)
- Ensure all functions have return type annotations

- [ ] **Step 4: Run full test suite with coverage**

```bash
cd projects/pdf-from-html && uv run pytest --cov=src/pdf_from_html --cov-report=term-missing -v
```

Expected: all tests pass, coverage shows which lines are covered.

- [ ] **Step 5: Commit any fixes**

```bash
git add projects/pdf-from-html/
git commit -m "chore(pdf-from-html): fix linting and type check issues"
```

(Skip this step if no changes were needed.)

- [ ] **Step 6: Final commit — mark project as complete**

```bash
git add -A
git commit -m "feat(pdf-from-html): complete v1 implementation

PDF from HTML API with:
- Single endpoint POST /v1/generate/pdf
- Raw HTML and URL source support
- Configurable page options (format, orientation, margins, scale, headers/footers)
- Playwright/Chromium rendering with browser pool
- SSRF prevention (http/https only)
- Full shared infrastructure integration (auth, rate limiting, metering)
- Comprehensive test suite"
```
