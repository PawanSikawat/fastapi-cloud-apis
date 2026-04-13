# Shared Infrastructure Architecture

## When to Consult
When creating a new API project, modifying the shared package, or debugging cross-cutting concerns (auth, billing, metering).

## Principles

1. **Every project imports shared as a path dependency.** No copy-paste, no forking. One source of truth.
2. **Middleware order is fixed:** ChannelDetect → RateLimit → Metering → Route handler. Changing this order breaks billing accuracy.
3. **Shared infra never contains business logic.** It handles auth, metering, rate limiting, and billing. The API route handler does the actual work.
4. **PostgreSQL for durable state, Redis for ephemeral state.** API keys, users, plans, usage aggregates → PostgreSQL. Rate limit counters, key cache, real-time usage → Redis.
5. **All shared dependencies come from FastAPI Cloud integrations.** PostgreSQL and Redis connection strings are injected via environment variables. No self-managed infrastructure.

## Patterns

### Adding shared to a new project

In `projects/<name>/pyproject.toml`:

```toml
[project]
dependencies = [
    "shared @ file://../../shared",
]
```

### Wiring shared into main.py

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI

from shared.auth.api_key import require_api_key
from shared.metering.middleware import MeteringMiddleware
from shared.rate_limit.middleware import RateLimitMiddleware
from shared.middleware.channel_detect import ChannelDetectMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize shared infra connections (Redis, PostgreSQL)
    # Store on app.state for access in dependencies
    yield
    # Close connections


app = FastAPI(lifespan=lifespan)

app.add_middleware(ChannelDetectMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MeteringMiddleware)

app.include_router(router, dependencies=[Depends(require_api_key)])
```

### Package structure

```
shared/
├── pyproject.toml
└── src/
    └── shared/
        ├── __init__.py
        ├── auth/           # API key validation, RapidAPI header validation
        ├── billing/        # Stripe client, webhooks, plan definitions
        ├── metering/       # Usage counting, quota enforcement
        ├── rate_limit/     # Token bucket / sliding window
        ├── middleware/      # Channel detection (RapidAPI vs direct)
        └── dependencies.py # Reusable Depends() callables
```

## Anti-Patterns

- **Importing project code from shared.** Shared depends on nothing except its own deps. Never import from `projects/`.
- **Adding business logic to middleware.** Middleware handles cross-cutting concerns only. If you're tempted to add "special handling for endpoint X" in middleware, put it in the route handler.
- **Using different PostgreSQL/Redis instances per project.** All projects share the same infrastructure databases for auth, billing, and metering. Project-specific data (if any) gets its own database.
- **Hardcoding plan limits in middleware.** Plan definitions live in `shared/billing/plans.py` and are loaded from the database. Middleware reads them dynamically.

## Checklist

- [ ] `shared` added as path dependency in `pyproject.toml`
- [ ] Middleware added in correct order: ChannelDetect → RateLimit → Metering
- [ ] Lifespan initializes and closes shared connections
- [ ] `require_api_key` dependency applied to all routes
- [ ] No project-specific logic in shared package
