# Monitoring on FastAPI Cloud

## When to Consult
When adding health checks, structured logging, error tracking, or debugging production issues.

## Principles

1. **Health check endpoint on every API.** `GET /health` returns 200 with service status, dependencies status, and uptime. FastAPI Cloud uses this for readiness checks.
2. **Structured logging with JSON.** Use Python's `logging` with a JSON formatter. Include request_id, api_key_hash (never the full key), endpoint, status_code, and response_time_ms.
3. **Request ID on every request.** Generate a UUID per request in middleware. Include it in all log entries and in the response header `X-Request-ID`. Consumers can reference it in support requests.
4. **Never log sensitive data.** API keys, request bodies with PII, authorization headers — none of these go in logs.
5. **Track business metrics alongside technical metrics.** Requests per API, revenue per API, conversion rates — not just latency and error rates.

## Patterns

### Health Check Endpoint

```python
@router.get("/health")
async def health(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> dict:
    db_ok = await check_db(db)
    redis_ok = await check_redis(redis)
    return {
        "status": "healthy" if (db_ok and redis_ok) else "degraded",
        "dependencies": {
            "postgresql": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
        "version": settings.project_name,
    }
```

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "api_key_hash"):
            log_data["api_key_hash"] = record.api_key_hash
        return json.dumps(log_data)
```

### Request ID Middleware

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

## Anti-Patterns

- **No health check.** FastAPI Cloud can't determine if your service is ready. Deploys may route traffic to unhealthy instances.
- **Logging full API keys.** Log only the first 8 characters or the hash. Full keys in logs are a security incident waiting to happen.
- **Unstructured log messages.** `print("something went wrong")` is useless in production. Structured JSON logs are searchable and parseable.
- **No request ID.** Without it, correlating a user's support request to server-side logs is nearly impossible.

## Checklist

- [ ] `GET /health` endpoint returns dependency status
- [ ] JSON structured logging configured
- [ ] Request ID middleware added (before other middleware)
- [ ] `X-Request-ID` returned in response headers
- [ ] No sensitive data in logs (keys, PII, auth headers)
- [ ] Response time logged per request
