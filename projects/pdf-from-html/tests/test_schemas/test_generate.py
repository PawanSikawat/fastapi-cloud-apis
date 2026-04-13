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
