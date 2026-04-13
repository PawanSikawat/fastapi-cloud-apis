# QR Code Generator API — Design Spec

## Overview

A QR code generation API that accepts parameters via multipart form, returns binary image output (PNG or SVG), and supports optional logo embedding for branded QR codes. Logo embedding is the primary competitive differentiator against existing RapidAPI offerings.

**Pattern:** Generator (parameters in, file out)
**Catalog score:** 4.55 (Tier 1) — Issue #6

---

## API Surface

### Endpoint

`POST /v1/generate/qrcode`

Content-Type: `multipart/form-data` (always — unified interface whether logo is present or not)

### Form Fields

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `data` | string | yes | — | 1–2953 characters (QR spec maximum) |
| `format` | string | no | `"png"` | `"png"` or `"svg"` |
| `size` | integer | no | `300` | 50–2000 (target output dimension in pixels; service calculates scale from QR matrix size) |
| `error_correction` | string | no | `"M"` | `"L"`, `"M"`, `"Q"`, `"H"` |
| `border` | integer | no | `4` | 0–10 (quiet zone width in modules) |
| `foreground_color` | string | no | `"#000000"` | 6-digit hex color with `#` prefix |
| `background_color` | string | no | `"#FFFFFF"` | 6-digit hex color with `#` prefix |
| `logo` | file | no | — | PNG, JPEG, or WEBP; max 500KB |
| `logo_size_ratio` | float | no | `0.25` | 0.1–0.4 (logo size as fraction of QR code size) |

### Behavior Rules

- When `logo` is provided, `error_correction` is automatically elevated to `"H"` (highest) regardless of the requested level. This ensures the QR code remains scannable with the center obscured by the logo.
- When `logo` is provided and `format` is `"svg"`, the API returns a `422` error. SVG output is vector-only; embedding a raster logo breaks the format's purpose.

### Response

- **Success (200):** Binary content with appropriate `Content-Type` header (`image/png` or `image/svg+xml`) and `Content-Disposition: inline; filename=qrcode.{format}`.
- **Validation error (422):** JSON error body: `{"error": "<ERROR_CODE>", "detail": "<human-readable message>"}`.

---

## Project Structure

```
projects/qr-code-generator/
├── pyproject.toml
├── src/qr_code_generator/
│   ├── __init__.py
│   ├── main.py              # App factory, lifespan, middleware stack
│   ├── config.py             # Settings(SharedSettings) + get_settings()
│   ├── exceptions.py         # AppError base + domain-specific errors
│   ├── routes/
│   │   ├── generate.py       # POST /v1/generate/qrcode
│   │   └── ui.py             # /ui/ login + generate page
│   ├── schemas/
│   │   └── generate.py       # QRCodeRequest model (for validation + OpenAPI docs)
│   ├── services/
│   │   └── generator.py      # QR generation, logo compositing, caching
│   ├── middleware/
│   │   └── cookie_auth.py    # CookieToHeaderMiddleware
│   ├── dependencies/
│   ├── static/
│   │   ├── css/pico.min.css
│   │   └── js/htmx.min.js
│   └── templates/
│       ├── login.html
│       └── generate.html
└── tests/
    ├── conftest.py
    ├── test_routes/
    │   └── test_generate.py
    ├── test_services/
    │   └── test_generator.py
    └── test_schemas/
        └── test_generate.py
```

---

## Configuration

```python
class Settings(SharedSettings):
    cache_ttl: int = 86400            # 24 hours
    max_logo_size: int = 512_000      # 500KB
    max_data_length: int = 2953       # QR spec limit
    cookie_secret_key: str = "dev-secret-change-in-production"
```

---

## Service Layer

### Library Choice

**`segno`** for QR code generation. It produces both PNG and SVG natively without extra dependencies, is faster than the `qrcode` library, and has a cleaner API. **`pillow`** is used only when a logo is provided, for image compositing.

### Generation Flow

1. Parse and validate form fields into a Pydantic model.
2. If logo is present and format is SVG, reject with `LogoSvgConflictError`.
3. If logo is present, auto-elevate error correction to `"H"`.
4. Compute cache key: SHA-256 of all parameters + logo bytes (if any).
5. Check Redis cache — return cached bytes on hit.
6. Generate QR code via `segno.make()`.
7. Serialize to requested format (PNG bytes via `segno` or SVG string via `segno`).
8. If logo is provided (PNG only):
   a. Open logo with Pillow, convert to RGBA.
   b. Calculate logo target size: `logo_size_ratio * qr_image_size`, preserving aspect ratio.
   c. Resize logo with `LANCZOS` resampling.
   d. Paste logo centered on QR image with alpha compositing.
   e. Re-serialize the composited image to PNG bytes.
9. Store result in Redis with `cache_ttl` expiry.
10. Return binary response.

### Caching Strategy

Cache key is derived from all input parameters:

```python
def _cache_key(params: dict, logo_bytes: bytes | None) -> str:
    payload = json.dumps(params, sort_keys=True)
    if logo_bytes:
        payload += hashlib.sha256(logo_bytes).hexdigest()
    return f"qr:{hashlib.sha256(payload.encode()).hexdigest()}"
```

Caching includes the logo bytes hash so identical logos with identical parameters produce cache hits.

---

## Error Handling

All custom exceptions inherit from `AppError`, following the established convention:

| Exception | Status | Error Code | Trigger |
|-----------|--------|------------|---------|
| `InvalidDataError` | 422 | `INVALID_DATA` | Data empty or exceeds 2953 chars |
| `InvalidColorError` | 422 | `INVALID_COLOR` | Malformed hex color string |
| `LogoTooLargeError` | 422 | `LOGO_TOO_LARGE` | Logo file exceeds 500KB |
| `LogoFormatError` | 422 | `LOGO_FORMAT_UNSUPPORTED` | Logo is not PNG, JPEG, or WEBP |
| `LogoSvgConflictError` | 422 | `LOGO_SVG_CONFLICT` | Logo provided with SVG output format |

---

## Middleware Stack

Identical to existing projects, from outermost to innermost:

1. **CookieToHeaderMiddleware** — reads signed cookie, injects `x-api-key` header
2. **ChannelDetectMiddleware** — sets `request.state.channel`
3. **AuthMiddleware** — validates API key
4. **RateLimitMiddleware** — per-minute rate limits
5. **MeteringMiddleware** — tracks API usage

---

## Web UI

### Pages

- **Login** (`GET /ui/login`, `POST /ui/login`) — same cookie-based auth flow as other projects. Pico CSS + simple form.
- **Generate** (`GET /ui/`, `POST /ui/generate`) — form with all QR code parameters:
  - Text input for data
  - Dropdown for format (PNG/SVG)
  - Sliders or number inputs for size, box_size, border
  - Color pickers for foreground/background
  - Dropdown for error correction level
  - File upload for logo
  - Slider for logo size ratio (shown only when logo is selected)
  - Live preview area showing the generated QR code
  - Download button

### Client-Side Validation

The UI validates the logo file before submitting to avoid wasting an API call:
- **File size:** Reject files over 500KB with an inline error message
- **File type:** Accept only PNG, JPEG, WEBP (check MIME type and extension)

Validation runs on file selection (`change` event on the file input), not on form submit — immediate feedback.

### Tech Stack

- **Pico CSS** for styling (consistent with other projects)
- **HTMX** for form submission and live preview without full page reload
- **Jinja2** templates

---

## Dependencies

### Python Packages

- `segno` — QR code generation (PNG + SVG)
- `pillow` — logo compositing (resize, paste, alpha blending)
- `python-multipart` — multipart form parsing (required by FastAPI for file uploads)
- Shared infra from `shared/` (auth, DB, Redis, middleware)

### Inherited from Shared

- `fastapi`, `uvicorn` — framework
- `redis` / `aioredis` — caching
- `sqlalchemy` + `aiosqlite` — database
- `httpx` — HTTP client
- `jinja2` — templates
- `itsdangerous` — signed cookies
- `pydantic-settings` — configuration

---

## Test Strategy

### Route Tests (`test_routes/test_generate.py`)

- **Happy path:** POST with just `data` field, verify 200 + PNG content type + valid PNG bytes
- **SVG output:** POST with `format=svg`, verify SVG content type + valid SVG markup
- **Logo upload:** POST with `data` + logo file, verify 200 + PNG with logo composited
- **Logo + SVG rejection:** POST with logo + `format=svg`, verify 422 + `LOGO_SVG_CONFLICT`
- **Custom colors:** POST with foreground/background colors, verify 200
- **Invalid color:** POST with `foreground_color=notacolor`, verify 422
- **Data too long:** POST with 3000-char data, verify 422 + `INVALID_DATA`
- **Missing data:** POST without `data` field, verify 422
- **Logo too large:** POST with >500KB logo, verify 422 + `LOGO_TOO_LARGE`
- **Logo bad format:** POST with `.gif` logo, verify 422 + `LOGO_FORMAT_UNSUPPORTED`
- **Error correction auto-elevation:** POST with logo + `error_correction=L`, verify the QR code uses H internally
- **Parameter boundaries:** size=50, size=2000, border=0, border=10

### Service Tests (`test_services/test_generator.py`)

- **Cache hit:** Generate once, call again with same params, verify Redis `get` is called and generation is skipped
- **Cache miss:** First call generates and stores in Redis
- **Logo compositing:** Provide a small test PNG, verify output image contains logo pixels at center
- **Error correction elevation:** Params with logo should use H regardless of input
- **Scale calculation:** Verify correct scale factor is derived from target `size` and QR matrix dimensions

### Schema Tests (`test_schemas/test_generate.py`)

- **Defaults applied:** Empty optional fields get correct defaults
- **Boundary validation:** size, box_size, border, logo_size_ratio min/max
- **Color validation:** Valid and invalid hex colors
- **Format validation:** Only `"png"` and `"svg"` accepted
- **Error correction validation:** Only `"L"`, `"M"`, `"Q"`, `"H"` accepted
