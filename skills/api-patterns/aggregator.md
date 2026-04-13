# Aggregator Pattern

## When to Consult
When building an API that combines data from multiple sources into a unified response. Examples: company enrichment (WHOIS + DNS + tech stack), URL metadata (OG tags + screenshot + security headers).

## Principles

1. **Fetch sources concurrently.** Use `asyncio.gather()` to call all sources in parallel. An aggregator that calls 3 sources sequentially is 3x slower than necessary.
2. **Partial results are better than no results.** If 2 of 3 sources succeed, return the 2 successful results with the failed source marked as `null` or `unavailable`. Don't fail the entire request.
3. **Normalize before aggregating.** Each source returns data in its own format. Normalize each source to a common schema before merging.
4. **Source-level caching.** Cache each source independently, not the aggregated result. Sources have different freshness requirements (WHOIS: 24h, DNS: 1h, tech stack: 12h).
5. **Document which sources are included.** The response should indicate which sources contributed data and which failed. Consumers need to know what they're getting.

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── enrich.py          # Single endpoint that aggregates
│   ├── schemas/
│   │   ├── request.py
│   │   └── response.py        # Aggregated response with source status
│   ├── services/
│   │   ├── sources/
│   │   │   ├── whois.py
│   │   │   ├── dns.py
│   │   │   └── tech_stack.py
│   │   └── aggregator.py      # Orchestrates concurrent fetch + merge
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Concurrent Fetch with Partial Failure

```python
import asyncio

async def aggregate(domain: str) -> AggregatedResult:
    results = await asyncio.gather(
        fetch_whois(domain),
        fetch_dns(domain),
        fetch_tech_stack(domain),
        return_exceptions=True,
    )

    whois = results[0] if not isinstance(results[0], Exception) else None
    dns = results[1] if not isinstance(results[1], Exception) else None
    tech = results[2] if not isinstance(results[2], Exception) else None

    return AggregatedResult(
        whois=whois,
        dns=dns,
        tech_stack=tech,
        sources={
            "whois": "ok" if whois else "error",
            "dns": "ok" if dns else "error",
            "tech_stack": "ok" if tech else "error",
        },
    )
```

### Response Schema

```python
class AggregatedResult(BaseModel):
    whois: WhoisData | None
    dns: DnsData | None
    tech_stack: TechStackData | None
    sources: dict[str, str]   # source_name -> "ok" | "error" | "cached"
```

## Anti-Patterns

- **Sequential source fetching.** `asyncio.gather()` exists. Use it.
- **All-or-nothing failure.** One slow or failed source shouldn't take down the entire response.
- **Caching the aggregated result as one blob.** Sources update at different rates. Cache each independently.
- **No source status in response.** Consumers need to know if the WHOIS data is missing because it failed or because the domain has privacy protection.

## Checklist

- [ ] All sources fetched concurrently via `asyncio.gather(return_exceptions=True)`
- [ ] Partial results returned when some sources fail
- [ ] `sources` field in response indicates status of each source
- [ ] Each source cached independently with appropriate TTL
- [ ] Each source has its own service module
- [ ] Source normalization happens before aggregation
