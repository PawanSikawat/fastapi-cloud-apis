import asyncio
import io

import httpx
from xhtml2pdf import pisa

from pdf_from_html.exceptions import RenderFailedError, RenderTimeoutError
from pdf_from_html.schemas.generate import PDFOptions

# Map API format names to CSS @page size keywords
_FORMAT_TO_CSS: dict[str, str] = {
    "A4": "a4",
    "Letter": "letter",
    "Legal": "legal",
    "Tabloid": "11in 17in",
}


def _build_page_css(options: PDFOptions) -> str:
    """Build a CSS @page rule from PDFOptions."""
    rules: list[str] = []

    if options.width is not None and options.height is not None:
        size = f"{options.width} {options.height}"
    else:
        size = _FORMAT_TO_CSS.get(options.format, "a4")

    if options.orientation == "landscape":
        size += " landscape"

    rules.append(f"size: {size}")
    rules.append(
        f"margin: {options.margin.top} {options.margin.right} "
        f"{options.margin.bottom} {options.margin.left}"
    )

    return f"@page {{ {'; '.join(rules)} }}"


def _render_pdf(source: str, content: str, options: PDFOptions) -> bytes:
    """Synchronous PDF rendering via xhtml2pdf (runs in a thread)."""
    if source == "url":
        response = httpx.get(content, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        html_content = response.text
    else:
        html_content = content

    page_css = _build_page_css(options)
    output = io.BytesIO()
    status = pisa.CreatePDF(html_content, dest=output, default_css=page_css)

    if status.err:
        raise RuntimeError(f"PDF generation produced {status.err} errors")

    return output.getvalue()


async def generate(
    source: str,
    content: str,
    options: PDFOptions,
    timeout: float,
) -> bytes:
    """Generate a PDF from HTML content or URL."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_render_pdf, source, content, options),
            timeout=timeout,
        )
    except TimeoutError:
        raise RenderTimeoutError(timeout) from None
    except Exception as exc:
        raise RenderFailedError(str(exc)) from None
