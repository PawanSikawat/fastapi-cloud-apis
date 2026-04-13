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
