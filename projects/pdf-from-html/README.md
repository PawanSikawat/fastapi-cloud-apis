# PDF from HTML API

Generate PDFs from raw HTML or URLs using Chromium with pixel-perfect rendering. Full CSS3 and JavaScript support via Playwright.

## Features

- **HTML to PDF** -- send raw HTML, get a PDF back
- **URL to PDF** -- render any public URL as a PDF
- **Pixel-perfect** -- Chromium-based rendering with full CSS3/JS support
- **Configurable** -- page size, margins, headers, footers, print background
- **Browser pool** -- reusable Chromium instances for fast response times
- **Web UI** -- browser-based interface for quick conversions

## API

### `POST /v1/generate/pdf`

Generate a PDF from HTML content or a URL.

### Example

```bash
# PDF from HTML
curl -X POST http://localhost:8000/v1/generate/pdf \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"html": "<h1>Hello World</h1><p>Generated PDF</p>"}' \
  -o output.pdf

# PDF from URL
curl -X POST http://localhost:8000/v1/generate/pdf \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"url": "https://example.com"}' \
  -o output.pdf
```

## Run Locally

```bash
# Install dependencies
uv sync

# Install Chromium for Playwright
uv run playwright install chromium

# Set environment variables
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"
export REDIS_URL="redis://localhost:6379/0"

# Start dev server
uv run fastapi dev src/pdf_from_html/main.py
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
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `COOKIE_SECRET_KEY` | Secret for web UI session cookies |

See the [root README](../../README.md) for the full list of shared environment variables.

## Tests

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/pdf_from_html --cov-report=term-missing

# Lint and type check
uv run ruff check . && uv run ruff format --check .
uv run mypy src/
```

## Dependencies

| Package | Purpose |
|---------|---------|
| playwright | Chromium browser automation for PDF rendering |
| jinja2 | Web UI templates |
| itsdangerous | Signed session cookies |
| shared | Auth, billing, metering, rate limiting |
