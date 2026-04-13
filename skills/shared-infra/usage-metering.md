# Usage Metering

## When to Consult
When implementing request counting, quota enforcement, or debugging usage discrepancies.

## Principles

1. **Meter every request, both channels.** RapidAPI and direct requests both count toward usage. Even though RapidAPI handles its own billing, metering gives you analytics.
2. **Redis for real-time counters, PostgreSQL for durable aggregates.** Increment Redis counter per request. Flush to PostgreSQL on a schedule (every 5 minutes) and on month rollover.
3. **Quota checks must be fast.** Read the current counter from Redis (O(1) operation). Never query PostgreSQL on the hot path for quota checks.
4. **Over-quota returns 429 with plan info.** Include current usage, plan limit, reset date, and upgrade URL in the response body.
5. **Monthly reset on calendar month.** Counters reset on the 1st of each month at 00:00 UTC. This is simple for users to understand and matches billing cycles.

## Patterns

### Redis Key Schema

```
usage:{api_key_hash}:{api_name}:{YYYY-MM}
```

Example: `usage:a1b2c3...:email-validator:2026-04`

Value: integer counter (INCR on each request).
TTL: 35 days (auto-cleanup of old months).

### Metering Middleware Flow

```
Request arrives (already authenticated)
  → Build Redis key from api_key_hash + api_name + current month
  → INCR the counter (atomic, returns new value)
  → Compare new value against plan limit
    → Under limit? Continue to route handler.
    → At/over limit?
      → Paid plan? Allow but flag for overage billing.
      → Free plan? Return 429 with quota exceeded response.
```

### Over-Quota Response (429)

```json
{
    "error": "quota_exceeded",
    "detail": "Monthly request limit reached",
    "usage": {
        "current": 101,
        "limit": 100,
        "resets_at": "2026-05-01T00:00:00Z"
    },
    "upgrade_url": "https://your-domain.com/pricing"
}
```

### Flush to PostgreSQL

Background task runs every 5 minutes:

```
For each active Redis usage key:
  → Read current value
  → UPSERT into PostgreSQL usage_records table
  → (Do NOT reset Redis — it's the source of truth until month rollover)
```

On month rollover (1st of month):
  → Final flush of previous month to PostgreSQL
  → Delete previous month's Redis keys

## Anti-Patterns

- **Querying PostgreSQL for quota checks.** Too slow on the hot path. Redis INCR is sub-millisecond.
- **Resetting counters on plan change.** If a user upgrades mid-month, update their limit, don't reset their count.
- **Losing usage data on Redis restart.** The 5-minute flush to PostgreSQL limits data loss to at most 5 minutes of counts. Acceptable for usage metering.
- **Metering only successful requests.** Meter all requests (including 4xx). The user consumed a request; they should know it.

## Checklist

- [ ] Redis INCR used for atomic counting
- [ ] Redis key includes api_key_hash, api_name, and YYYY-MM
- [ ] TTL set on Redis keys (35 days)
- [ ] 429 response includes usage object with current, limit, resets_at
- [ ] Background flush to PostgreSQL every 5 minutes
- [ ] Monthly rollover handled cleanly
