# Data Proxy Pattern

## When to Consult
When building an API that fetches data from an external source, transforms it, and serves it to the consumer. Examples: email validation, IP geolocation, phone validation, currency conversion.

## Principles

1. **Cache aggressively.** External data changes slowly — IP geolocation is valid for days, WHOIS data for hours. Cache in Redis with appropriate TTLs.
2. **Never expose the upstream source.** The consumer doesn't need to know you're wrapping MaxMind or querying DNS directly. Your API is the interface.
3. **Graceful degradation when upstream fails.** Serve stale cache rather than returning 503. Add a `cached: true` field to the response if serving stale data.
4. **Normalize upstream responses.** Different sources return data in different formats. Your API returns a consistent schema regardless of which source was used.
5. **Validate inputs before calling upstream.** Don't waste an external API call on an obviously invalid email or malformed IP address.

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── validate.py        # or lookup.py, enrich.py
│   ├── schemas/
│   │   ├── request.py         # Input validation schemas
│   │   └── response.py        # Normalized output schemas
│   ├── services/
│   │   ├── provider.py        # External data source client
│   │   └── cache.py           # Redis caching layer
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Caching Layer

```python
import hashlib
import json

async def cached_lookup(
    redis: Redis,
    cache_key: str,
    ttl: int,
    fetch_fn,
) -> tuple[dict, bool]:
    """Returns (data, was_cached)."""
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached), True

    data = await fetch_fn()
    await redis.setex(cache_key, ttl, json.dumps(data))
    return data, False
```

### Response Schema

```python
class ProxyResponse(BaseModel):
    data: DataModel        # The actual result
    cached: bool = False   # Whether served from cache
    credits_used: int = 1  # For credit-based billing
```

## Anti-Patterns

- **No caching.** Every request hits the upstream source. Slow, expensive, and you'll get rate-limited by the upstream.
- **Exposing upstream errors directly.** "MaxMind returned 403" means nothing to your consumer. Map upstream errors to your own error codes.
- **Unbounded cache TTL.** Stale data erodes trust. Set TTLs based on how frequently the data actually changes.
- **No input validation.** Calling an external API with garbage input wastes money and time.

## Checklist

- [ ] Input validated before external call
- [ ] Redis cache with appropriate TTL per data type
- [ ] Stale cache served when upstream fails (with `cached: true`)
- [ ] Upstream errors mapped to your own error codes
- [ ] Response schema is consistent regardless of source
- [ ] External API client reused via lifespan (httpx.AsyncClient)
