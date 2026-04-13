# FastAPI Cloud Deployment

## When to Consult
When deploying a new API project to FastAPI Cloud, configuring environment variables, or troubleshooting deployment issues.

## Principles

1. **One FastAPI Cloud app per project.** Each project in `projects/` deploys independently. They share the shared infra package but are separate deployments.
2. **FastAPI Cloud auto-discovers the app.** It looks for a `FastAPI()` instance in `main.py`. No special configuration needed.
3. **Environment variables for all configuration.** Database URLs, Redis URLs, Stripe keys, RapidAPI secrets — all injected via FastAPI Cloud dashboard, consumed via Pydantic Settings.
4. **The `shared/` package ships with each project.** It's a path dependency in `pyproject.toml`. FastAPI Cloud installs it as part of the project's dependencies.
5. **Never commit secrets.** Use `.env.example` to document required variables. `.env` is in `.gitignore`.

## Patterns

### Project pyproject.toml

```toml
[project]
name = "email-validator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]",
    "pydantic-settings",
    "httpx",
    "shared @ file://../../shared",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
strict = true
python_version = "3.12"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### .env.example

```env
# Injected by FastAPI Cloud
APP_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
APP_REDIS_URL=redis://host:6379/0

# Configure in FastAPI Cloud dashboard
APP_STRIPE_SECRET_KEY=sk_test_...
APP_STRIPE_WEBHOOK_SECRET=whsec_...
APP_RAPIDAPI_PROXY_SECRET=your-proxy-secret

# Project-specific
APP_PROJECT_NAME=email-validator
```

### Config Pattern

```python
from functools import cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: str
    redis_url: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    rapidapi_proxy_secret: str
    project_name: str

@cache
def get_settings() -> Settings:
    return Settings()
```

## Anti-Patterns

- **Hardcoding connection strings.** Even for development. Use `.env` files locally, FastAPI Cloud dashboard in production.
- **Multiple FastAPI apps in one deployment.** Each project deploys separately. Don't try to serve multiple APIs from one app.
- **Committing `.env` files.** `.env` is in `.gitignore`. Only `.env.example` (with placeholder values) is committed.
- **Installing shared as a git submodule.** Path dependency is simpler and faster. `shared @ file://../../shared` works locally and on FastAPI Cloud.

## Checklist

- [ ] `pyproject.toml` includes `shared` as path dependency
- [ ] `.env.example` documents all required environment variables
- [ ] `.env` is in `.gitignore`
- [ ] Pydantic Settings class uses `env_prefix="APP_"`
- [ ] Settings loaded via `@cache`-decorated function
- [ ] `main.py` has a `FastAPI()` instance at module level
