import io
from typing import TYPE_CHECKING, Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from pdf_from_html.config import Settings, get_settings
from pdf_from_html.exceptions import ContentTooLargeError, InvalidURLError
from pdf_from_html.schemas.generate import PDFGenerateRequest
from pdf_from_html.services.pdf_service import generate

if TYPE_CHECKING:
    from pdf_from_html.services.browser_pool import BrowserPool

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
