# Rate Limiting

## When to Consult
When implementing rate limiting, adjusting limits per plan, or debugging 429 errors that aren't quota-related.

## Principles

1. **Rate limiting and quota limiting are different.** Quota = total requests per month. Rate limit = requests per second/minute. Both enforce via 429 but with different response bodies.
2. **Use sliding window algorithm.** Token bucket allows bursts that can overwhelm downstream services. Sliding window provides smoother traffic shaping.
3. **Rate limits are per API key, per API.** A user's email-validator key and qr-generator key have independent rate limits.
4. **Limits scale with plan tier.** Free: 10 req/min. Basic: 60 req/min. Pro: 300 req/min. Enterprise: custom.
5. **Rate limit headers on every response.** Include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` so clients can self-throttle.

## Patterns

### Sliding Window Counter (Redis)

```
Key: ratelimit:{api_key_hash}:{api_name}:{window_timestamp}
Value: request count in this window
TTL: 2 * window_size (auto-cleanup)
```

Window size: 60 seconds. Check current window + previous window, weighted by overlap.

### Rate Limit Response Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1714580400
```

### Rate Limited Response (429)

```json
{
    "error": "rate_limited",
    "detail": "Too many requests",
    "retry_after": 3,
    "rate_limit": {
        "limit": 60,
        "remaining": 0,
        "reset": 1714580400
    }
}
```

Include `Retry-After` header (seconds until the client can retry).

### Plan-Based Limits

| Plan | Requests/Minute | Burst Allowance |
|------|----------------|-----------------|
| Free | 10 | None |
| Basic | 60 | 10 extra |
| Pro | 300 | 50 extra |
| Enterprise | Custom | Custom |

## Anti-Patterns

- **Global rate limit instead of per-key.** One abusive user shouldn't affect others. Always per-key.
- **No rate limit headers.** Without headers, clients can't self-throttle and will hammer the API until they get 429s.
- **Rate limiting after the route handler runs.** Rate limit check must happen in middleware, before any business logic executes.
- **Same error format for rate limit and quota exceeded.** They're different situations. Rate limited = slow down. Quota exceeded = upgrade or wait for month reset.

## Checklist

- [ ] Sliding window algorithm implemented in Redis
- [ ] Limits configured per plan tier
- [ ] `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers on all responses
- [ ] `Retry-After` header on 429 responses
- [ ] Rate limit 429 body distinct from quota 429 body
- [ ] Middleware executes before route handler
