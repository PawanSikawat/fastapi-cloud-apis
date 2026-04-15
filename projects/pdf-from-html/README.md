# PDF from HTML API

Generate PDFs from raw HTML or URLs using server-side HTML/CSS rendering via `xhtml2pdf`.

## Features

- **HTML to PDF** -- send raw HTML, get a PDF back
- **URL to PDF** -- render any public URL as a PDF
- **HTML/CSS rendering** -- convert raw HTML into PDFs without a browser dependency
- **Configurable** -- page size, margins, headers, footers, print background
- **Simple server runtime** -- no browser pool or Playwright install required
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

# Set environment variables
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"
export REDIS_URL="redis://localhost:6379/0"

# Start dev server
uv run fastapi dev pdf_from_html/main.py
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
uv run pytest --cov=pdf_from_html --cov-report=term-missing

# Lint and type check
uv run ruff check . && uv run ruff format --check .
uv run mypy pdf_from_html/
```

## Dependencies

| Package | Purpose |
|---------|---------|
| xhtml2pdf | Server-side HTML to PDF rendering |
| jinja2 | Web UI templates |
| itsdangerous | Signed session cookies |
| shared | Auth, billing, metering, rate limiting |
