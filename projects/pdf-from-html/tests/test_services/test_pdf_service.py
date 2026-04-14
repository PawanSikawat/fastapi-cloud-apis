from unittest.mock import MagicMock, patch

import pytest


class TestBuildPageCSS:
    def test_defaults(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_page_css

        css = _build_page_css(PDFOptions())
        assert "size: a4" in css
        assert "landscape" not in css
        assert "margin: 20mm 20mm 20mm 20mm" in css

    def test_landscape(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_page_css

        css = _build_page_css(PDFOptions(orientation="landscape"))
        assert "a4 landscape" in css

    def test_letter_format(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_page_css

        css = _build_page_css(PDFOptions(format="Letter"))
        assert "size: letter" in css

    def test_tabloid_uses_explicit_dimensions(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_page_css

        css = _build_page_css(PDFOptions(format="Tabloid"))
        assert "size: 11in 17in" in css

    def test_custom_dimensions_override_format(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _build_page_css

        css = _build_page_css(PDFOptions(width="100mm", height="200mm"))
        assert "size: 100mm 200mm" in css
        assert "a4" not in css

    def test_custom_margins(self) -> None:
        from pdf_from_html.schemas.generate import Margin, PDFOptions
        from pdf_from_html.services.pdf_service import _build_page_css

        css = _build_page_css(
            PDFOptions(margin=Margin(top="10mm", right="15mm", bottom="10mm", left="15mm"))
        )
        assert "margin: 10mm 15mm 10mm 15mm" in css


class TestRenderPdf:
    def test_raw_html_calls_create_pdf(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _render_pdf

        mock_status = MagicMock()
        mock_status.err = 0

        with patch("pdf_from_html.services.pdf_service.pisa") as mock_pisa:
            mock_pisa.CreatePDF.return_value = mock_status
            _render_pdf("raw", "<html>Hi</html>", PDFOptions())

        mock_pisa.CreatePDF.assert_called_once()
        call_args = mock_pisa.CreatePDF.call_args
        assert call_args.args[0] == "<html>Hi</html>"

    def test_url_fetches_then_renders(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _render_pdf

        mock_status = MagicMock()
        mock_status.err = 0
        mock_response = MagicMock()
        mock_response.text = "<html>Fetched</html>"

        with (
            patch("pdf_from_html.services.pdf_service.pisa") as mock_pisa,
            patch("pdf_from_html.services.pdf_service.httpx") as mock_httpx,
        ):
            mock_httpx.get.return_value = mock_response
            mock_pisa.CreatePDF.return_value = mock_status
            _render_pdf("url", "https://example.com", PDFOptions())

        mock_httpx.get.assert_called_once_with(
            "https://example.com", follow_redirects=True, timeout=30.0
        )
        call_args = mock_pisa.CreatePDF.call_args
        assert call_args.args[0] == "<html>Fetched</html>"

    def test_page_css_passed_as_default_css(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _render_pdf

        mock_status = MagicMock()
        mock_status.err = 0

        with patch("pdf_from_html.services.pdf_service.pisa") as mock_pisa:
            mock_pisa.CreatePDF.return_value = mock_status
            _render_pdf("raw", "<html>test</html>", PDFOptions())

        call_kwargs = mock_pisa.CreatePDF.call_args.kwargs
        assert "default_css" in call_kwargs
        assert "@page" in call_kwargs["default_css"]

    def test_errors_raise_runtime_error(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import _render_pdf

        mock_status = MagicMock()
        mock_status.err = 3

        with (
            patch("pdf_from_html.services.pdf_service.pisa") as mock_pisa,
            pytest.raises(RuntimeError, match="3 errors"),
        ):
            mock_pisa.CreatePDF.return_value = mock_status
            _render_pdf("raw", "<html>bad</html>", PDFOptions())


class TestGenerate:
    async def test_returns_pdf_bytes(self) -> None:
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        with patch(
            "pdf_from_html.services.pdf_service._render_pdf",
            return_value=b"%PDF-1.4 test",
        ):
            result = await generate("raw", "<html>Hi</html>", PDFOptions(), timeout=30.0)
        assert result == b"%PDF-1.4 test"

    async def test_timeout_raises_render_timeout(self) -> None:
        from pdf_from_html.exceptions import RenderTimeoutError
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        def slow_render(*_args: object, **_kwargs: object) -> bytes:
            import time

            time.sleep(5)
            return b""

        with (
            patch("pdf_from_html.services.pdf_service._render_pdf", side_effect=slow_render),
            pytest.raises(RenderTimeoutError),
        ):
            await generate("raw", "<html>slow</html>", PDFOptions(), timeout=0.1)

    async def test_render_error_raises_render_failed(self) -> None:
        from pdf_from_html.exceptions import RenderFailedError
        from pdf_from_html.schemas.generate import PDFOptions
        from pdf_from_html.services.pdf_service import generate

        with (
            patch(
                "pdf_from_html.services.pdf_service._render_pdf",
                side_effect=RuntimeError("bad html"),
            ),
            pytest.raises(RenderFailedError),
        ):
            await generate("raw", "<html>bad</html>", PDFOptions(), timeout=30.0)
