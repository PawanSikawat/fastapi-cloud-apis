# Email Validation API

Production-grade email validation with syntax checks, MX record lookup, SMTP verification, disposable email detection, and role-based email detection.

## Features

- **Syntax validation** -- RFC-compliant email format checking
- **MX record lookup** -- verify the domain accepts email
- **SMTP verification** -- check if the mailbox exists (without sending)
- **Disposable detection** -- flag temporary/throwaway email providers
- **Role-based detection** -- identify generic addresses (info@, admin@, support@)
- **Batch processing** -- validate multiple emails in a single request
- **Web UI** -- browser-based interface for quick validations

## API

### `POST /v1/validate/email`

Validate a single email address.

### `POST /v1/validate/email/batch`

Validate multiple email addresses in one request.

### Example

```bash
# Single email validation
curl -X POST http://localhost:8000/v1/validate/email \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"email": "user@example.com"}'

# Batch validation
curl -X POST http://localhost:8000/v1/validate/email/batch \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"emails": ["alice@gmail.com", "bob@tempmail.org", "info@company.com"]}'
```

## Run Locally

```bash
# Install dependencies
uv sync

# Set environment variables
export APP_DATABASE_URL="sqlite+aiosqlite:///./dev.db"
export APP_REDIS_URL="redis://localhost:6379/0"

# Start dev server
uv run fastapi dev src/email_validation/main.py
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
uv run pytest --cov=src/email_validation --cov-report=term-missing

# Lint and type check
uv run ruff check . && uv run ruff format --check .
uv run mypy src/
```

## Dependencies

| Package | Purpose |
|---------|---------|
| dnspython | DNS/MX record lookups |
| jinja2 | Web UI templates |
| itsdangerous | Signed session cookies |
| shared | Auth, billing, metering, rate limiting |
