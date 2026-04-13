from playwright._impl._api_structures import PdfMargins
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from typing_extensions import TypedDict

from pdf_from_html.exceptions import RenderFailedError, RenderTimeoutError
from pdf_from_html.schemas.generate import PDFOptions
from pdf_from_html.services.browser_pool import BrowserPool


class _PdfKwargs(TypedDict, total=False):
    """Typed kwargs for Playwright Page.pdf() — keeps mypy happy on **-unpacking."""

    format: str | None
    landscape: bool | None
    scale: float | None
    print_background: bool | None
    margin: PdfMargins | None
    page_ranges: str | None
    display_header_footer: bool | None
    header_template: str | None
    footer_template: str | None
    width: str | float | None
    height: str | float | None


def _build_pdf_options(options: PDFOptions) -> _PdfKwargs:
    """Convert PDFOptions into Playwright page.pdf() kwargs."""
    margin: PdfMargins = {
        "top": options.margin.top,
        "right": options.margin.right,
        "bottom": options.margin.bottom,
        "left": options.margin.left,
    }

    pdf_opts: _PdfKwargs = {
        "format": options.format,
        "landscape": options.orientation == "landscape",
        "margin": margin,
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
                await page.set_content(content, wait_until="networkidle", timeout=timeout_ms)

            pdf_options = _build_pdf_options(options)
            return await page.pdf(**pdf_options)
        except PlaywrightTimeoutError:
            raise RenderTimeoutError(timeout) from None
        except PlaywrightError as exc:
            raise RenderFailedError(str(exc)) from None
