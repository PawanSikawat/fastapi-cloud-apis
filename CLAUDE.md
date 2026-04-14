# CLAUDE.md

## Project Purpose

fastapi-cloud-apis is a collection of production-grade FastAPI projects, each integrating with different cloud services and APIs. The repo serves as an accumulation of multiple independent FastAPI applications under a single monorepo.

**Each project must be self-contained, well-tested, and production-ready.**

## Expert Hat Principle

For every prompt, identify which expert roles are needed and think from those perspectives before responding:

- **API Designer** — RESTful conventions, endpoint design, request/response schemas, HTTP semantics
- **System Architect** — project boundaries, async patterns, dependency management, data flow
- **Python Engineer** — idiomatic Python, type safety, async/await patterns, error handling
- **Cloud/Infra Engineer** — cloud service integration, authentication, rate limiting, resilience
- **Security Engineer** — no hardcoded credentials, input validation, dependency auditing, OWASP top 10

**Process:** Read the prompt -> identify applicable hats -> think deeply from each perspective -> critically self-review your answer -> fix any issues -> present with confidence.

Do NOT ask the user to validate domain decisions. Make the right call.

## Workspace Structure

This is a monorepo containing multiple independent FastAPI projects:

```
fastapi-cloud-apis/
├── CLAUDE.md
├── projects/
│   └── <project-name>/
│       ├── pyproject.toml        # Project-level dependencies and config
│       ├── <package_name>/
│       │   ├── __init__.py
│       │   ├── main.py       # FastAPI app factory, lifespan, router includes
│       │   ├── config.py     # Pydantic Settings — env vars, validation
│       │   ├── routes/       # Route modules grouped by domain
│       │   ├── schemas/      # Pydantic request/response models
│       │   ├── services/     # Business logic, external API clients
│       │   ├── models/       # Database models (SQLAlchemy/SQLModel if needed)
│       │   ├── dependencies/ # FastAPI dependency injection functions
│       │   └── exceptions.py # Custom exception classes and handlers
│       └── tests/
│           ├── conftest.py
│           ├── test_routes/
│           └── test_services/
└── shared/                       # Optional shared utilities across projects
    └── ...
```

### Project Independence

Each project under `projects/` is self-contained with its own `pyproject.toml`, virtual environment, and test suite. Projects do not import from each other. Shared code, if any, lives in `shared/` and is kept minimal.

## Commands

```bash
# All commands run from within a specific project directory: projects/<project-name>/

# Install dependencies (use uv for speed)
uv sync

# Run dev server
uv run fastapi dev <package_name>/main.py

# Test
uv run pytest

# Test with coverage
uv run pytest --cov=<package_name> --cov-report=term-missing

# Format
uv run ruff format .

# Lint
uv run ruff check . --fix

# Type check
uv run mypy <package_name>/
```

## Code Quality Standard

- Correctness first — subtle bugs in API logic, auth, or data handling break trust
- No shortcuts on error handling — use custom exception classes and FastAPI exception handlers
- Think about failure modes: what if the external API returns unexpected data? If the DB connection drops mid-request? If the request body is malformed?
- No hardcoded credentials, tokens, or API keys — ever. Use Pydantic Settings with env vars
- No bare `except:` or `except Exception:` that swallows errors silently
- Public API endpoints must have Pydantic schemas for both request and response

## Type Safety

Use type hints everywhere. FastAPI relies on them for validation, serialization, and documentation.

```python
# Good — fully typed
async def get_user(user_id: int) -> UserResponse:
    ...

# Bad — untyped
async def get_user(user_id):
    ...
```

- All function signatures must have parameter types and return types
- Use Pydantic `BaseModel` for all request/response schemas
- Use `Annotated[T, Depends(...)]` for dependency injection
- Prefer `str | None` over `Optional[str]` (Python 3.10+ union syntax)

## Pydantic Convention

All data validation and serialization goes through Pydantic v2.

| Layer | Pattern |
|-------|---------|
| **Config** | `pydantic_settings.BaseSettings` with `SettingsConfigDict()` (no env prefix — matches FastAPI Cloud conventions) |
| **Request bodies** | `pydantic.BaseModel` subclasses in `schemas/` |
| **Response models** | `pydantic.BaseModel` subclasses in `schemas/`, referenced in route `response_model` |
| **Internal data** | Dataclasses or Pydantic models depending on validation needs |

**Naming** — suffix schemas by purpose: `UserCreate`, `UserUpdate`, `UserResponse`, `UserInDB`.

## Module Boundaries

- `config.py` — Pydantic Settings class only. No logic. Loaded once via `lru_cache` or `functools.cache`.
- `routes/` — thin layer. Parse request, call service, return response. No business logic.
- `services/` — all business logic. Named by domain (`user_service.py`, `payment_service.py`).
- `schemas/` — Pydantic models only. No logic beyond validators.
- `dependencies/` — FastAPI `Depends()` callables. Auth, DB sessions, rate limiters.
- `main.py` — app factory, lifespan handler, router includes. Minimal code.

## Dependency Injection

Use FastAPI's `Depends()` system consistently:

```python
from typing import Annotated
from fastapi import Depends

# Define dependency
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Use via Annotated
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

async def get_users(db: DbSession) -> list[UserResponse]:
    ...
```

## Error Handling

Define structured error responses. Never leak internal details to clients.

```python
# Custom exception
class AppException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code

# Register handler in main.py
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.detail},
    )
```

## Async Convention

Use `async def` for all route handlers and service functions that perform I/O. Use `def` only for purely synchronous CPU-bound operations.

- HTTP clients: `httpx.AsyncClient` (reuse via lifespan/dependency, never recreate per request)
- Database: async SQLAlchemy or async SQLModel sessions
- File I/O: `aiofiles` when needed
- Never use `requests` library in async code — use `httpx`

## Performance

- Reuse HTTP clients — create `httpx.AsyncClient` in lifespan, store in `app.state`, close on shutdown
- Connection pooling — async DB engine with pool_size configured
- Streaming responses — use `StreamingResponse` for large payloads
- Background tasks — use FastAPI `BackgroundTasks` for fire-and-forget work
- Middleware order matters — put lightweight middleware (CORS) before heavy ones (auth)

## Dependency & Toolchain Policy

Always use the **latest stable versions** of Python, FastAPI, and all dependencies. When adding new dependencies, pull the newest published version. When modifying `pyproject.toml`, check if existing packages have newer versions and upgrade them. Avoid pinning to old versions unless there is a documented compatibility reason.

- **Python**: 3.13+ (use latest stable)
- **Package manager**: `uv`
- **Framework**: FastAPI with Uvicorn
- **Linting/Formatting**: Ruff (replaces black, isort, flake8)
- **Type checking**: mypy (strict mode)
- **Testing**: pytest + pytest-asyncio + httpx (for `TestClient`)

## Documenting Deviations

When code intentionally deviates from the project's normal conventions or expected patterns (e.g., using sync code where async is the convention, skipping validation that's normally required, using `Any` where strict typing is the convention), add a comment **directly above the deviation** explaining **why** the exception exists.

```python
# DEVIATION: sync function despite I/O — this runs in a subprocess
# and async would add complexity without benefit
def generate_report(data: ReportData) -> bytes:
    ...

# DEVIATION: bare dict return instead of Pydantic model — health check
# endpoint intentionally returns minimal unstructured response
@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

## Testing

- Every route must have tests for: happy path, validation errors, auth failures, edge cases
- Use `httpx.AsyncClient` with `ASGITransport` for async test client
- Use `pytest.fixture` for shared setup (test DB, mock services, auth tokens)
- Mock external services at the HTTP boundary (`respx` or `httpx` mock), not at the service layer
- Test file structure mirrors source: `test_routes/test_users.py` tests `routes/users.py`

```python
# Test pattern
@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

async def test_create_user(client: AsyncClient) -> None:
    response = await client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"
```

## FastAPI Cloud Deployment

Every project must be deployable to FastAPI Cloud out of the box. Follow these conventions when building new projects:

### Project Layout (Flat, Not src/)

Use **flat layout** — the package directory sits at the project root, NOT inside `src/`. This is critical for FastAPI Cloud's module discovery.

```
projects/<project-name>/
├── pyproject.toml
├── <package_name>/       # ← flat layout, directly importable
│   ├── __init__.py
│   ├── main.py
│   └── ...
└── tests/
```

**Never use `src/` layout** for deployed apps. It breaks FastAPI Cloud's auto-import unless you configure the directory setting.

### pyproject.toml Requirements

```toml
[tool.fastapi]
entrypoint = "<package_name>.main:app"

[tool.hatch.build.targets.wheel]
packages = ["<package_name>"]
```

- Entrypoint must use **module import format** (`package.main:app`), not file paths
- The `app` object must be a module-level variable in `main.py` (via `app = create_app()`)

### Environment Variables (No Prefix)

FastAPI Cloud auto-provisions `DATABASE_URL` and `REDIS_URL` without any prefix. Pydantic Settings must use **no env prefix**:

```python
class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict()  # no env_prefix
    database_url: str
    redis_url: str
```

### Database URL Normalization

FastAPI Cloud sets `DATABASE_URL` with `postgresql://` scheme and `?sslmode=require`, but async SQLAlchemy with asyncpg needs `postgresql+asyncpg://` and does not accept `sslmode` (it uses `ssl` instead). The shared package auto-normalizes both the scheme and query parameters in `shared/database.py`.

### Root URL Redirect

Every project must redirect `GET /` to `/ui/login`:

```python
@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse("/ui/login", status_code=302)
```

Add `"/"` to `_AUTH_SKIP_PATHS`.

### Auth Skip Paths

These paths must always be in `_AUTH_SKIP_PATHS`:

```python
_AUTH_SKIP_PATHS = frozenset({
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/webhooks/stripe",
    "/ui/login",
    "/ui/logout",
})
```

### Cookie Middleware

The `CookieToHeaderMiddleware` must skip redirect for both `/ui/login` and `/ui/logout` — logout must work even without a valid cookie.

### Admin User Seeding

Every app auto-creates an admin user and API key on startup via `setup_shared()`. This is handled entirely by the shared package — no per-project code needed.

**Required env var on FastAPI Cloud:**
- `ADMIN_API_KEY` — any string (e.g. `sk_<random>`). The app hashes it and registers it on startup. Idempotent — safe across restarts/redeployments.

**Optional:**
- `ADMIN_EMAIL` — defaults to `admin@local`

The admin user gets `plan="admin"`. Tables are auto-created on startup via `Base.metadata.create_all` (idempotent).

**Generate a key locally:**
```bash
python -c "import secrets; print(f'sk_{secrets.token_urlsafe(32)}')"
```

### Deploy Command

```bash
# From repo root:
./deploy.sh <project-name>

# Or manually from project directory:
uv lock --upgrade-package shared
uv run fastapi cloud deploy
```

When prompted for directory, leave it **empty** (flat layout means the package is at the project root).

### Deploy Checklist

Before deploying a new project, verify these env vars are set in FastAPI Cloud:

1. `DATABASE_URL` — auto-provisioned by FastAPI Cloud
2. `REDIS_URL` — auto-provisioned by FastAPI Cloud
3. `ADMIN_API_KEY` — your admin key (required for first login)
4. `COOKIE_SECRET_KEY` — secret for signing session cookies
5. `ADMIN_EMAIL` — optional, defaults to `admin@local`

## Skills

Domain expertise is encoded in skill files under `skills/`:

- `skills/api-business/` — Pricing strategies, competitor analysis, conversion optimization
- `skills/shared-infra/` — Auth, billing, metering, rate limiting architecture
- `skills/api-patterns/` — Data proxy, AI wrapper, document processor, generator, aggregator
- `skills/fastapi-cloud/` — Deployment, scaling, monitoring on FastAPI Cloud
- `skills/marketplace/` — RapidAPI publishing, documentation standards, SEO
- `skills/api-catalog/` — API opportunity catalog, evaluation criteria, scoring

**Consult the relevant skill before making domain decisions.**

## Keeping This File Up to Date

Whenever you add a new project, change the workspace structure, introduce new patterns, or change any fundamental convention, update this file immediately.

## GitHub Issues as Source of Truth

Track **all** work as GitHub issues — features, bugs, enhancements, and announcements. This ensures continuity across sessions; any session can be closed and resumed later with full context.

- **Before starting work**: create a GitHub issue describing the feature, bug, or task with enough detail that someone (or a future session) can pick it up cold.
- **During work**: reference the issue number in commits and PRs.
- **Discoveries**: if you find a bug or identify a follow-up while working on something else, file a separate issue immediately rather than losing the context.
- **Labels**: use `bug`, `enhancement`, `feature`, `chore` as appropriate.
- Use `gh issue create` via CLI. Keep titles short, put detail in the body.

## GitHub Operations

Use `gh auth switch --user PawanSikawat` before GitHub operations (push, PR, repo creation), then switch back to `gh auth switch --user pawan-dt` after.
