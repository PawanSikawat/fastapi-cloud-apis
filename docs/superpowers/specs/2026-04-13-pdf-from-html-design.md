# PDF from HTML API — Design Spec

**Date:** 2026-04-13
**Project:** `projects/pdf-from-html/`
**Pattern:** Generator (parameters in, file out)
**Catalog score:** 4.15 (Tier 1)

> **Status note (2026-04-15):** This spec captures the original intended
> Playwright/Chromium architecture. The current implementation in
> `projects/pdf-from-html/` uses `xhtml2pdf` instead. Treat this file as design
> history unless and until the browser-based renderer is intentionally restored.

## Summary

A production-grade API that converts raw HTML or a URL into a PDF file. The
original design targeted Playwright/Chromium for pixel-perfect browser rendering.
The currently shipped implementation uses `xhtml2pdf` for server-side HTML/CSS
rendering. It remains a synchronous request-response API: one POST, one PDF back.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Rendering engine | Playwright/Chromium (planned) | Original target architecture for browser-grade CSS/JS fidelity; not the current shipped renderer. |
| Input model | Single endpoint, `source` discriminator | Cleaner than two endpoints. `source: "raw"` or `"url"` with `content` field. |
| Response model | Synchronous, PDF bytes | Generator pattern: return file directly. 30s timeout covers 95%+ of real-world renders. |
| Batch support | Not in v1 | Single conversion covers primary use case. Merge endpoint is a v2 candidate. |
| Templates | Not in v1 | Server-side templates deferred. Users handle templating client-side. |
| Page options | Standard tier | Format, orientation, margins, scale, backgrounds, page ranges, headers/footers, custom dimensions. |

## API Surface

### `POST /v1/generate/pdf`

**Request body:**

```json
{
  "source": "raw",
  "content": "<html><body><h1>Hello</h1></body></html>",
  "options": {
    "format": "A4",
    "orientation": "portrait",
    "margin": {
      "top": "20mm",
      "right": "20mm",
      "bottom": "20mm",
      "left": "20mm"
    },
    "scale": 1.0,
    "print_background": true,
    "page_ranges": null,
    "header_html": null,
    "footer_html": null,
    "width": null,
    "height": null
  }
}
```

**Fields:**

- `source` (required): `"raw"` or `"url"`
- `content` (required): HTML string if `source` is `"raw"`, HTTP(S) URL if `source` is `"url"`
- `options` (optional): all fields have sensible defaults, entire object is optional

**Response:**

- `200 OK` with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="document.pdf"`
- Body: raw PDF bytes

**Error responses:**

All errors return JSON: `{"error": "ERROR_CODE", "detail": "Human-readable message"}`

| Status | Error Code | Condition |
|--------|------------|-----------|
| 401 | `UNAUTHORIZED` | Missing or invalid API key (shared middleware) |
| 403 | `FORBIDDEN` | Inactive API key (shared middleware) |
| 422 | `INVALID_SOURCE` | `source` is not "raw" or "url" |
| 422 | `INVALID_URL` | `source` is "url" but `content` isn't valid HTTP(S) URL |
| 422 | `CONTENT_TOO_LARGE` | Raw HTML exceeds 5MB |
| 429 | `RATE_LIMIT_EXCEEDED` | Rate limit hit (shared middleware) |
| 429 | `QUOTA_EXCEEDED` | Monthly quota exhausted (shared middleware) |
| 502 | `RENDER_FAILED` | HTML-to-PDF render failure |
| 503 | `POOL_EXHAUSTED` | Planned browser pool exhausted (not used by current implementation) |
| 504 | `RENDER_TIMEOUT` | Render exceeded timeout (default 30s) |

## Architecture

### Data Flow

```
Request → ChannelDetect → Auth → RateLimit → Metering → Route Handler
                                                              │
                                                              ▼
                                                       Validate input
                                                       (source + content)
                                                              │
                                                              ▼
                                                    PDFService.generate()
                                                              │
                                                       ┌──────┴──────┐
                                                       │   source?   │
                                                    raw│             │url
                                                       ▼             ▼
                                                set_content()     goto()
                                                       │             │
                                                       └──────┬──────┘
                                                              ▼
                                                      page.pdf(options)
                                                              │
                                                              ▼
                                                    StreamingResponse
```

### Components

- **Route handler** (`routes/generate.py`): validates input, calls PDFService, returns StreamingResponse. Thin layer, no business logic.
- **PDFService** (`services/pdf_service.py`): orchestrates render. Acquires browser context from pool, creates page, loads content via `set_content()` (raw) or `goto()` (URL), applies PDF options, calls `page.pdf()`, returns bytes.
- **BrowserPool** (`services/browser_pool.py`): manages reusable Playwright browser contexts. Created in lifespan, stored in `app.state`. Uses an asyncio semaphore to cap concurrency. Avoids cold-starting browsers per request.
- **Lifespan**: launches Playwright Chromium and creates BrowserPool on startup. Closes everything on shutdown. Also runs `setup_shared()` for DB/Redis/auth.

### Security

- **SSRF prevention**: URL source only allows `http://` and `https://` schemes. Blocks `file://`, `data:`, `javascript:`.
- **Size limit**: Raw HTML capped at 5MB.
- **Browser isolation**: Playwright runs Chromium with default security (sandbox enabled). Network access allowed for external CSS/images but browser process is isolated.

## Configuration

All settings extend `SharedSettings`, configurable via `APP_`-prefixed env vars:

```python
class Settings(SharedSettings):
    # Browser pool
    browser_pool_size: int = 3              # max concurrent browser contexts

    # Render limits
    render_timeout: float = 30.0            # seconds before RenderTimeoutError
    max_content_size: int = 5_242_880       # 5MB max raw HTML size

    # PDF defaults
    default_format: str = "A4"
    default_orientation: str = "portrait"
    default_margin_top: str = "20mm"
    default_margin_right: str = "20mm"
    default_margin_bottom: str = "20mm"
    default_margin_left: str = "20mm"
    default_scale: float = 1.0
    default_print_background: bool = True
```

## Project Structure

```
projects/pdf-from-html/
├── pyproject.toml
├── src/pdf_from_html/
│   ├── __init__.py
│   ├── main.py                  # App factory, lifespan (browser + shared), middleware
│   ├── config.py                # Settings extending SharedSettings
│   ├── exceptions.py            # AppError subclasses
│   ├── routes/
│   │   ├── __init__.py
│   │   └── generate.py          # POST /v1/generate/pdf
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── generate.py          # PDFGenerateRequest, PDFOptions, Margin
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py       # generate() — orchestrates render
│   │   └── browser_pool.py      # BrowserPool — manages Playwright contexts
│   └── dependencies/
│       └── __init__.py
└── tests/
    ├── conftest.py              # App fixture with mocked browser pool
    ├── test_routes/
    │   └── test_generate.py     # Route tests (mock service layer)
    └── test_services/
        ├── test_pdf_service.py  # Service orchestration tests
        └── test_browser_pool.py # Pool lifecycle tests
```

## Dependencies

### Runtime
- `fastapi[standard]>=0.115.0`
- `pydantic-settings>=2.7.0`
- `playwright>=1.52.0`
- `shared` (local editable)

### Dev
- `pytest`, `pytest-asyncio`
- `httpx` (test client)
- `mypy`, `ruff`
- `fakeredis`, `aiosqlite`

## Testing Strategy

- **Route tests**: mock `pdf_service.generate()`, return fake PDF bytes. Validate request parsing, response headers, error codes, auth enforcement.
- **Service tests**: mock `BrowserPool`, verify correct Playwright method calls for raw vs URL, options mapping, timeout handling, render failure handling.
- **Pool tests**: test acquire/release lifecycle, semaphore exhaustion, context reuse.
- **No real Playwright in unit tests**: all Chromium calls are mocked. Integration tests with a real browser are out of v1 scope.

## Pricing

Adjusted for high-compute (per pricing-strategies skill):

| Tier | PDFs/month | Price | Overage |
|------|-----------|-------|---------|
| Free | 50 | $0 | Hard cutoff |
| Basic | 5,000 | $19/mo | $0.005/PDF |
| Pro | 50,000 | $49/mo | $0.003/PDF |
| Enterprise | Custom | Custom | Custom |

## Future Features (deferred)

See memory file `project_pdf_api_future_features.md` for the full list. Key v2 candidates:
- Server-side templates with variable substitution
- Batch conversion / PDF merge
