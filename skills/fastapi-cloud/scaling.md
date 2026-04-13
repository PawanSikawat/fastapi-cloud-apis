# Scaling on FastAPI Cloud

## When to Consult
When an API is under load, optimizing for cold starts, or planning capacity for a high-traffic API.

## Principles

1. **Async everywhere for I/O.** FastAPI's concurrency model handles thousands of concurrent connections — but only if your code is non-blocking. One synchronous `requests.get()` blocks the entire worker.
2. **CPU-bound work goes to thread/process pool.** Image processing, PDF generation, ML inference — use `asyncio.to_thread()` to avoid blocking the event loop.
3. **Connection reuse is critical.** Create `httpx.AsyncClient` and database connections in the lifespan handler. Reuse across requests. Never create per-request.
4. **Cache to reduce compute.** Redis cache for repeat requests (same QR code parameters, same email validation) avoids redundant work.
5. **Cold starts matter for serverless-style scaling.** Keep imports minimal at module level. Lazy-load heavy dependencies (ML models) in the lifespan handler.

## Patterns

### Lifespan Pattern for Connection Reuse

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    # Initialize DB, Redis, etc.
    yield
    # Shutdown
    await app.state.http_client.aclose()
```

### CPU-Bound Work in Thread Pool

```python
import asyncio
from PIL import Image

async def process_image(data: bytes) -> bytes:
    # Runs in a separate thread, doesn't block event loop
    return await asyncio.to_thread(_process_image_sync, data)

def _process_image_sync(data: bytes) -> bytes:
    img = Image.open(io.BytesIO(data))
    # ... CPU-heavy processing ...
    return output_bytes
```

### Lazy Model Loading

```python
_model = None

async def get_model():
    global _model
    if _model is None:
        _model = await asyncio.to_thread(load_heavy_model)
    return _model
```

## Anti-Patterns

- **Using `requests` library in async code.** It's synchronous and blocks the event loop. Use `httpx.AsyncClient`.
- **Creating a new database connection per request.** Connection creation takes 50-200ms. Use a pool.
- **Loading ML models at import time.** Slows cold starts. Load in lifespan or lazily on first request.
- **Unbounded concurrency on external APIs.** Use `asyncio.Semaphore` to cap concurrent calls to upstream services that have rate limits.

## Checklist

- [ ] All I/O operations are async
- [ ] CPU-bound work uses `asyncio.to_thread()`
- [ ] HTTP clients created in lifespan, reused across requests
- [ ] Database connections pooled
- [ ] Redis connection reused
- [ ] Heavy models loaded lazily or in lifespan
- [ ] External API calls bounded by semaphore if upstream has rate limits
