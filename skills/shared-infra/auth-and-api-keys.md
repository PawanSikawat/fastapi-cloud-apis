# Auth and API Keys

## When to Consult
When implementing API key generation, validation, rotation, or debugging auth failures.

## Principles

1. **API keys are the only auth mechanism for API consumers.** No OAuth, no JWT, no session cookies. API key in `X-API-Key` header (direct channel) or RapidAPI headers (marketplace channel).
2. **Keys are hashed in the database.** Store SHA-256 hash, never plaintext. Show the full key exactly once at creation time.
3. **Every key belongs to a user and a plan.** The plan determines rate limits and quotas. Upgrading the plan upgrades the key's limits immediately.
4. **Key validation must be fast.** Cache valid keys in Redis with a 5-minute TTL. A cache miss hits PostgreSQL and refreshes the cache.
5. **Revoked keys must be rejected immediately.** When a key is revoked, delete it from Redis cache. The next request will miss the cache and find it revoked in PostgreSQL.

## Patterns

### API Key Format

```
prefix_<32 random hex chars>

Example: fca_a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
```

- Prefix `fca_` (fastapi-cloud-apis) makes keys identifiable in logs and leak detection tools.
- 32 hex chars = 128 bits of entropy.

### Validation Flow

```
Request arrives
  → Check X-RapidAPI-Proxy-Secret header
    → Present? Validate proxy secret, extract X-RapidAPI-User. Done.
    → Absent? Check X-API-Key header.
      → Present? Look up in Redis cache.
        → Cache hit + valid? Allow. Attach user/plan to request state.
        → Cache miss? Look up hash in PostgreSQL.
          → Found + active? Cache in Redis (5min TTL). Allow.
          → Not found or revoked? Return 401.
      → Absent? Return 401.
```

### Key Data Model

```python
class ApiKeyRecord:
    id: str              # UUID
    key_hash: str        # SHA-256 of the full key
    user_id: str         # Owner
    plan_id: str         # Current plan
    created_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None
```

## Anti-Patterns

- **Storing plaintext keys.** If the database leaks, every customer is compromised. Hash with SHA-256.
- **API key in query parameters.** Keys in URLs end up in server logs, browser history, and CDN caches. Header only.
- **Long-lived keys with no rotation.** Offer key rotation (generate new key, grace period for old key, then revoke old key).
- **Blocking on PostgreSQL for every request.** Redis cache is mandatory. Without it, auth adds 5-50ms latency per request.

## Checklist

- [ ] Keys prefixed with `fca_` for identification
- [ ] Keys stored as SHA-256 hashes in PostgreSQL
- [ ] Redis cache with 5-minute TTL for active keys
- [ ] Revocation deletes from Redis immediately
- [ ] Full key shown exactly once at creation time
- [ ] 401 response body includes error code and message (not just status code)
