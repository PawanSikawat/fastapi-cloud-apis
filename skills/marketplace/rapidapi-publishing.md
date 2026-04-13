# RapidAPI Publishing

## When to Consult
When listing a new API on RapidAPI, updating an existing listing, or optimizing for marketplace conversion.

## Principles

1. **Import your OpenAPI spec.** FastAPI auto-generates it at `/openapi.json`. RapidAPI can import this directly. Don't manually define endpoints on RapidAPI.
2. **Use the standard pricing tier template.** Free (100 req/mo), Basic ($9/mo, 10k), Pro ($29/mo, 100k), Enterprise (custom). Adjust only for high-compute APIs.
3. **The API name is your SEO.** "Email Validation API" beats "EmailChecker Pro" — users search for what the API does, not brand names.
4. **One API = one RapidAPI listing.** Don't bundle unrelated APIs into one listing. Separate listings get separate discovery.
5. **Configure the proxy secret immediately.** Set `X-RapidAPI-Proxy-Secret` in RapidAPI dashboard and your environment variables. Without this, your API is open to header spoofing.

## Patterns

### Publishing Checklist (in order)

1. Deploy the API to FastAPI Cloud
2. Verify `/openapi.json` is accessible
3. Create a new API on RapidAPI Hub
4. Import OpenAPI spec from your deployed URL
5. Configure base URL to point to your FastAPI Cloud deployment
6. Set `X-RapidAPI-Proxy-Secret` in Security settings
7. Configure pricing tiers (Free, Basic, Pro, Enterprise)
8. Add API description, category, and tags
9. Add example requests with realistic data
10. Test each endpoint via RapidAPI's test console
11. Publish and submit for marketplace review

### Pricing Tier Setup

| Tier | Name on RapidAPI | Rate Limit | Monthly Quota |
|------|-----------------|------------|---------------|
| Free | "Basic" (RapidAPI's free tier label) | 10 req/min | 100 requests |
| Basic | "Pro" | 60 req/min | 10,000 requests |
| Pro | "Ultra" | 300 req/min | 100,000 requests |
| Enterprise | "Mega" | Custom | Custom |

Note: RapidAPI uses its own tier names. Map your plan names to theirs.

### Description Template

```
[One-line description of what the API does]

## Features
- [Feature 1]
- [Feature 2]
- [Feature 3]

## Use Cases
- [Use case 1]
- [Use case 2]

## Quick Start
1. Subscribe to a plan
2. Copy your API key
3. Make your first request:

[curl example]
```

## Anti-Patterns

- **Manually defining endpoints on RapidAPI.** Import the OpenAPI spec. Manual definitions get out of sync with your actual API.
- **No free tier.** RapidAPI users expect to try before buying. No free tier = no signups.
- **Ignoring RapidAPI's test console.** Test every endpoint from RapidAPI's dashboard before publishing. It catches CORS, auth, and routing issues.
- **Generic API description.** "A powerful API for data processing" tells users nothing. Be specific: "Validate email addresses — MX record lookup, SMTP verification, disposable email detection."

## Checklist

- [ ] OpenAPI spec imported (not manually defined)
- [ ] Proxy secret configured in both RapidAPI and FastAPI Cloud
- [ ] 4 pricing tiers configured
- [ ] Every endpoint tested via RapidAPI test console
- [ ] Description includes features, use cases, and quick start
- [ ] Category and tags set for discoverability
