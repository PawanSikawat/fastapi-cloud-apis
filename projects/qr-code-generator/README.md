# QR Code Generator API

Generate QR codes with optional logo embedding. Supports PNG and SVG output with full customization of colors, size, border, and error correction levels.

## Features

- **PNG and SVG output** -- choose the format that fits your use case
- **Logo embedding** -- overlay a logo on QR codes with automatic error correction elevation
- **Customizable** -- colors, size (50-2000px), border, error correction (L/M/Q/H)
- **Redis caching** -- identical requests are served from cache
- **Web UI** -- browser-based interface with live preview and download

## API

### `POST /v1/generate/qrcode`

Multipart form endpoint. Returns the generated QR code image.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `data` | string | *(required)* | URL or text to encode (1-2953 chars) |
| `format` | string | `png` | Output format: `png` or `svg` |
| `size` | int | `300` | Target size in pixels (50-2000) |
| `error_correction` | string | `M` | Error correction: `L`, `M`, `Q`, `H` |
| `border` | int | `4` | Border width in modules (0-10) |
| `foreground_color` | string | `#000000` | QR code color (hex) |
| `background_color` | string | `#ffffff` | Background color (hex) |
| `logo` | file | *(optional)* | Logo image (PNG, JPEG, or WebP, max 500KB) |
| `logo_size_ratio` | float | `0.25` | Logo size relative to QR code (0.1-0.4) |

**Notes:**
- When a logo is provided, error correction is automatically elevated to `H` for scan reliability
- Logo embedding is only supported with PNG output; `logo` + `format=svg` returns 422

### Example

```bash
# Simple QR code
curl -X POST http://localhost:8000/v1/generate/qrcode \
  -F "data=https://example.com" \
  -o qrcode.png

# QR code with logo and custom colors
curl -X POST http://localhost:8000/v1/generate/qrcode \
  -F "data=https://example.com" \
  -F "foreground_color=#1a1a2e" \
  -F "background_color=#e2e2e2" \
  -F "logo=@logo.png" \
  -F "size=500" \
  -o qrcode_with_logo.png

# SVG output
curl -X POST http://localhost:8000/v1/generate/qrcode \
  -F "data=https://example.com" \
  -F "format=svg" \
  -o qrcode.svg
```

## Run Locally

```bash
# Install dependencies
uv sync

# Set environment variables
export APP_DATABASE_URL="sqlite+aiosqlite:///./dev.db"
export APP_REDIS_URL="redis://localhost:6379/0"

# Start dev server
uv run fastapi dev src/qr_code_generator/main.py
```

- API docs: http://127.0.0.1:8000/docs
- Web UI: http://127.0.0.1:8000/ui/login
- Health check: http://127.0.0.1:8000/health

## Deploy to FastAPI Cloud

```bash
uv run fastapi cloud deploy
```

Then configure environment variables in the FastAPI Cloud dashboard:

| Variable | Description |
|----------|-------------|
| `APP_DATABASE_URL` | PostgreSQL connection string |
| `APP_REDIS_URL` | Redis connection string |
| `APP_COOKIE_SECRET_KEY` | Secret for web UI session cookies |

See the [root README](../../README.md) for the full list of shared environment variables.

## Tests

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/qr_code_generator --cov-report=term-missing

# Lint and type check
uv run ruff check . && uv run ruff format --check .
uv run mypy src/
```

65 tests covering schemas, services, routes, caching, and UI (92% coverage).

## Dependencies

| Package | Purpose |
|---------|---------|
| segno | QR code generation (PNG + SVG) |
| pillow | Logo compositing on PNG output |
| python-multipart | Multipart form parsing |
| jinja2 | Web UI templates |
| itsdangerous | Signed session cookies |
| shared | Auth, billing, metering, rate limiting |
