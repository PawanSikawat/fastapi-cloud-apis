# fastapi-cloud-apis

A collection of production-grade FastAPI APIs, each integrating with different cloud services. Built for deployment on [FastAPI Cloud](https://fastapi.cloud).

## Projects

| Project | Description | Endpoints |
|---------|-------------|-----------|
| [QR Code Generator](projects/qr-code-generator/) | Generate QR codes with optional logo embedding (PNG/SVG) | `POST /v1/generate/qrcode` |
| [PDF from HTML](projects/pdf-from-html/) | Generate PDFs from raw HTML or URLs using HTML/CSS rendering | `POST /v1/generate/pdf` |
| [Email Validation](projects/email-validation/) | Validate emails with syntax, MX, SMTP, disposable, and role-based checks | `POST /v1/validate/email`, `POST /v1/validate/email/batch` |

Each project is self-contained with its own dependencies, test suite, and web UI.

## Repository Structure

```
fastapi-cloud-apis/
├── projects/
│   ├── qr-code-generator/    # QR code generation with logo support
│   ├── pdf-from-html/        # HTML/URL to PDF conversion
│   └── email-validation/     # Email validation suite
├── shared/                   # Auth, billing, metering, rate limiting
└── skills/                   # Domain expertise documentation
```

## Shared Infrastructure

All projects depend on the `shared/` package which provides:

- **Authentication** -- API key validation, RapidAPI proxy auth
- **Billing** -- Stripe integration, plan management
- **Rate Limiting** -- Per-minute request limits by plan
- **Usage Metering** -- API call tracking and quota enforcement
- **Channel Detection** -- RapidAPI vs direct channel routing

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL (production) or SQLite (development/testing)
- Redis

## Quick Start

Each project runs independently. Pick one and follow its README, or use the commands below.

## Starting A New API

Use the shared starter path instead of bootstrapping from scratch:

- Playbook: [docs/new-api-playbook.md](/Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/docs/new-api-playbook.md)
- Template: [templates/api-starter/README.md](/Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/templates/api-starter/README.md)

### Run Locally

```bash
# Navigate to a project
cd projects/qr-code-generator

# Install dependencies
uv sync

# Set required environment variables
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"
export REDIS_URL="redis://localhost:6379/0"

# Start the dev server
uv run fastapi dev qr_code_generator/main.py
```

The API docs are available at `http://127.0.0.1:8000/docs` and the web UI at `http://127.0.0.1:8000/ui/login`.

### Run Tests

```bash
cd projects/qr-code-generator

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=qr_code_generator --cov-report=term-missing
```

### Code Quality

```bash
cd projects/qr-code-generator

# Lint
uv run ruff check . --fix

# Format
uv run ruff format .

# Type check
uv run mypy qr_code_generator/
```

## Deploy to FastAPI Cloud

Each project deploys as a separate FastAPI Cloud app.

### 1. Install the FastAPI CLI

```bash
pip install fastapi-cli
```

### 2. Deploy a project

```bash
cd projects/qr-code-generator
uv run fastapi cloud deploy
```

FastAPI Cloud auto-discovers the `app` instance in `main.py`. Each project uses the
repo-local `shared/` package as a path dependency, so shared infrastructure changes
travel with the monorepo.

### 3. Configure environment variables

Set these in the [FastAPI Cloud dashboard](https://fastapi.cloud) for each deployed app:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis connection string |
| `STRIPE_SECRET_KEY` | Stripe secret key for billing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `RAPIDAPI_PROXY_SECRET` | RapidAPI proxy secret (if publishing to RapidAPI) |
| `COOKIE_SECRET_KEY` | Secret for signing web UI session cookies |

### 4. Verify deployment

```bash
curl https://your-app.fastapi.cloud/health
# {"status": "ok"}
```

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Validation**: Pydantic v2
- **Database**: SQLAlchemy (async) + PostgreSQL
- **Caching**: Redis
- **Payments**: Stripe
- **Package Manager**: uv
- **Linting**: Ruff
- **Type Checking**: mypy (strict)
- **Testing**: pytest + pytest-asyncio

## License

Private repository.
