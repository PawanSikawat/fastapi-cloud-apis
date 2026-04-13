# Skills System & Paid API Platform Design

## Overview

A skills system for `fastapi-cloud-apis` — a monorepo of paid FastAPI services hosted on FastAPI Cloud, distributed via both RapidAPI marketplace and a self-hosted branded channel.

### Goals

- Encode domain expertise so any session can build, ship, and monetize a new API without re-learning patterns
- Maintain a living catalog of API opportunities ranked by revenue potential
- Provide shared infrastructure (auth, billing, metering, rate limiting) that every project plugs into
- Support dual-channel distribution: RapidAPI marketplace + direct API key sales

### Non-Goals

- Building a full SaaS platform with user dashboards (keep it API-first)
- Custom deployment infrastructure (FastAPI Cloud handles this)
- Cross-project data sharing (each API is independent)

---

## 1. Skills Directory Structure

```
skills/
├── api-business/
│   ├── pricing-strategies.md
│   ├── competitor-analysis.md
│   └── conversion-optimization.md
│
├── shared-infra/
│   ├── architecture.md
│   ├── auth-and-api-keys.md
│   ├── usage-metering.md
│   ├── rate-limiting.md
│   ├── billing-stripe.md
│   └── rapidapi-compatibility.md
│
├── api-patterns/
│   ├── data-proxy.md
│   ├── ai-wrapper.md
│   ├── document-processor.md
│   ├── generator.md
│   └── aggregator.md
│
├── fastapi-cloud/
│   ├── deployment.md
│   ├── scaling.md
│   └── monitoring.md
│
├── marketplace/
│   ├── rapidapi-publishing.md
│   ├── api-documentation.md
│   └── seo-and-discovery.md
│
└── api-catalog/
    ├── README.md
    ├── catalog.md
    └── evaluation-criteria.md
```

### Skill File Format

Every skill file follows a consistent structure:

```markdown
# Skill Title

## When to Consult
One-line trigger — when should this skill be read?

## Principles
Numbered list of decision rules.

## Patterns
Code examples with explanation. Copy-paste ready.

## Anti-Patterns
What NOT to do, with reasoning.

## Checklist
Steps to verify the skill was applied correctly.
```

---

## 2. Shared Infrastructure

### Package Structure

```
shared/
├── pyproject.toml
└── src/
    └── shared/
        ├── __init__.py
        ├── auth/
        │   ├── __init__.py
        │   ├── api_key.py          # API key validation dependency
        │   ├── rapidapi.py         # RapidAPI proxy-secret header validation
        │   └── models.py           # ApiKey, Plan, User schemas
        ├── billing/
        │   ├── __init__.py
        │   ├── stripe_client.py    # Stripe customer, subscription, invoice management
        │   ├── webhooks.py         # Stripe webhook handler (subscription changes, failures)
        │   └── plans.py            # Plan definitions (free, basic, pro, enterprise)
        ├── metering/
        │   ├── __init__.py
        │   ├── counter.py          # Request counting, quota check
        │   ├── storage.py          # Usage storage backend (PostgreSQL + Redis)
        │   └── middleware.py       # FastAPI middleware that meters every request
        ├── rate_limit/
        │   ├── __init__.py
        │   ├── limiter.py          # Token bucket / sliding window per API key
        │   └── middleware.py       # FastAPI middleware for rate limiting
        ├── middleware/
        │   ├── __init__.py
        │   └── channel_detect.py   # Detect if request is from RapidAPI or direct
        └── dependencies.py         # Reusable FastAPI Depends() for all of the above
```

### Data Layer

Uses FastAPI Cloud's managed integrations:

- **PostgreSQL** — API keys, users, plans, usage records (monthly aggregates per key per API), billing state (Stripe customer/subscription IDs)
- **Redis** — rate limiting state (token buckets/sliding windows), real-time usage counters (flushed to PostgreSQL periodically), API key validation cache (avoid DB lookup per request)

No self-managed database infrastructure. FastAPI Cloud injects connection credentials via environment variables.

### How a Project Plugs In

Each project adds `shared` as a path dependency:

```toml
# projects/<name>/pyproject.toml
[project]
dependencies = [
    "shared @ file://../../shared",
    # ... project-specific deps
]
```

Wiring in `main.py`:

```python
from shared.auth.api_key import require_api_key
from shared.metering.middleware import MeteringMiddleware
from shared.rate_limit.middleware import RateLimitMiddleware
from shared.middleware.channel_detect import ChannelDetectMiddleware

app = FastAPI(lifespan=lifespan)

# Middleware stack (order matters — outermost first)
app.add_middleware(ChannelDetectMiddleware)   # detect RapidAPI vs direct
app.add_middleware(RateLimitMiddleware)        # enforce rate limits
app.add_middleware(MeteringMiddleware)         # count usage

# All routes require a valid API key
app.include_router(router, dependencies=[Depends(require_api_key)])
```

### Dual-Channel Detection

Every incoming request is tagged as `direct` or `rapidapi`:

- **RapidAPI**: detected by `X-RapidAPI-Proxy-Secret` header. Auth handled by RapidAPI — shared layer validates the proxy secret and extracts subscriber identity from `X-RapidAPI-User`.
- **Direct**: standard API key in `X-API-Key` header. Auth, billing, and metering fully managed by shared layer + Stripe.

Metering and rate limiting apply to both channels. Billing only applies to direct customers (RapidAPI handles its own billing).

---

## 3. API Catalog

The catalog is the strategic core — it decides what gets built next.

### Evaluation Criteria

Every API opportunity is scored on four dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| **Demand** | 35% | Search volume, RapidAPI category popularity, developer forum mentions |
| **Margin** | 25% | Cost to serve per request vs. price users pay |
| **Competition** | 25% | Number of alternatives, their pricing, quality gaps |
| **Build Complexity** | 15% | Estimated effort to build and maintain |

Each dimension scored 1-5. Weighted total gives priority rank.

### Tier Structure

- **Tier 1 (Score 4.0+)** — Build next
- **Tier 2 (Score 3.0-3.9)** — Build soon
- **Tier 3 (Score < 3.0)** — Backlog
- **Shipped** — Live APIs with launch date

### Initial Catalog (27 APIs)

All tracked as GitHub issues with `API idea` label (issues #1-#27).

**Data Proxy / Enrichment (5):**

| API | Score | Key Angle |
|-----|-------|-----------|
| Email Validation (#1) | 4.55 | 10x cheaper than Hunter.io |
| IP Geolocation & Threat Intel (#2) | 4.15 | Bundle geo + threat in one call |
| URL Metadata Extraction (#5) | 4.00 | One endpoint for rich link previews |
| Phone Number Validation (#4) | 3.95 | Fraction of Twilio Lookup pricing |
| Company/Domain Enrichment (#3) | 3.40 | Clearbit alternative using open data |

**Generators (5):**

| API | Score | Key Angle |
|-----|-------|-----------|
| QR Code Generator (#6) | 4.55 | Styled QR codes with logo embedding via API |
| Barcode Generation (#10) | 4.35 | All formats in one API |
| Invoice/Receipt Generation (#8) | 4.20 | API-first, no full accounting SaaS needed |
| PDF from HTML/Templates (#7) | 4.15 | Template library included, request-based pricing |
| Screenshot-as-a-Service (#9) | 3.70 | Cheaper than ScreenshotAPI at scale |

**AI Wrappers (5):**

| API | Score | Key Angle |
|-----|-------|-----------|
| Sentiment Analysis (#14) | 3.80 | Single-purpose, no NLP platform signup |
| OCR / Text Extraction (#11) | 3.65 | Simple flat pricing, no cloud lock-in |
| Image Background Removal (#12) | 3.60 | 5-10x cheaper than remove.bg |
| Text Summarization (#13) | 3.25 | Dead-simple text transformation API |
| Language Detection & Translation (#15) | 3.05 | Simpler pricing than Google Cloud Translation |

**Document Processors (4):**

| API | Score | Key Angle |
|-----|-------|-----------|
| CSV/Excel to JSON (#18) | 4.35 | Upload file, get JSON — no ETL platform |
| Image Compression & Conversion (#17) | 4.30 | 10x TinyPNG volume at same price |
| PDF to Text/Images (#16) | 4.10 | Flat-rate vs. Adobe's per-page pricing |
| Markdown to PDF/HTML (#19) | 4.05 | API-first rendering with themes |

**Developer Utilities (5):**

| API | Score | Key Angle |
|-----|-------|-----------|
| Cron Expression Parser (#22) | 4.00 | Niche, sticky, near-zero cost to serve |
| JSON Schema Validation (#23) | 4.00 | Server-side validation for no-code platforms |
| Placeholder Image Generation (#24) | 4.00 | More customizable than placeholder.com |
| URL Shortener with Analytics (#20) | 3.85 | API-first with analytics, cheaper than Bitly |
| Webhook Relay & Inspection (#21) | 3.80 | Programmable forwarding, API-first |

**Finance (3):**

| API | Score | Key Angle |
|-----|-------|-----------|
| IBAN / Bank Account Validation (#27) | 4.20 | Algorithmic — near-zero cost, undercut ibanapi.com |
| Tax Rate Lookup (#26) | 3.80 | Simple lookup, not full tax platform |
| Currency Conversion (#25) | 3.75 | Generous free tier |

---

## 4. FastAPI Cloud Deployment

### Project Structure

```
projects/<project-name>/
├── pyproject.toml           # Dependencies (includes shared as path dep)
├── src/<package_name>/
│   ├── main.py              # FastAPI app — FastAPI Cloud auto-discovers this
│   └── ...
└── .env.example             # Documents required env vars (never committed with values)
```

### Environment Variables

Each project uses Pydantic Settings with consistent naming:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    # Injected by FastAPI Cloud
    database_url: str
    redis_url: str

    # Configured in FastAPI Cloud dashboard
    stripe_secret_key: str
    stripe_webhook_secret: str
    rapidapi_proxy_secret: str

    # Project-specific
    project_name: str = "email-validator"
```

### Deployment Model

- Each project deploys as a separate FastAPI Cloud app
- The `shared/` package ships with each project as a path dependency (not a separate deployment)
- PostgreSQL and Redis connections injected by FastAPI Cloud
- Secrets configured in FastAPI Cloud dashboard, exposed as env vars

---

## 5. Marketplace Publishing

### RapidAPI Request Flow

```
API Consumer
     │
     ├── RapidAPI ──> X-RapidAPI-Proxy-Secret + X-RapidAPI-User headers
     │
     └── Direct ───> X-API-Key header
     │
     ▼
ChannelDetectMiddleware (tags as "rapidapi" or "direct")
     │
RateLimitMiddleware (enforces per-key, per-plan limits)
     │
MeteringMiddleware (counts usage for both channels)
     │
FastAPI Route Handler
```

### Pricing Tier Template

Every API uses the same tier structure on RapidAPI:

| Tier | Requests/Month | Target User |
|------|---------------|-------------|
| **Free** | 100 | Testing and evaluation |
| **Basic** ($9/mo) | 10,000 | Hobbyist / early startup |
| **Pro** ($29/mo) | 100,000 | Production usage |
| **Enterprise** | Custom | High-volume, SLA, support |

Actual pricing adjusted per API based on cost-to-serve.

### Documentation Requirements

Every API ships with:
- OpenAPI spec auto-generated by FastAPI (RapidAPI imports this directly)
- At least 3 example requests per endpoint with realistic data
- Error code reference table
- Rate limit and quota documentation
- Getting started guide (under 5 minutes to first successful call)

---

## 6. CLAUDE.md Updates Required

After skills are implemented, add to CLAUDE.md:

```markdown
## Skills

Domain expertise is encoded in skill files under `skills/`:

- `skills/api-business/` — Pricing strategies, competitor analysis, conversion optimization
- `skills/shared-infra/` — Auth, billing, metering, rate limiting architecture
- `skills/api-patterns/` — Data proxy, AI wrapper, document processor, generator, aggregator
- `skills/fastapi-cloud/` — Deployment, scaling, monitoring on FastAPI Cloud
- `skills/marketplace/` — RapidAPI publishing, documentation standards, SEO
- `skills/api-catalog/` — API opportunity catalog, evaluation criteria, scoring

**Consult the relevant skill before making domain decisions.**
```

---

## 7. Build Order

1. **shared/** infrastructure package (auth, metering, rate limiting, billing) — foundation for everything
2. **skills/** directory with all skill files — guides all subsequent work
3. **First Tier 1 API** (Email Validation — score 4.55, simplest to build, highest demand)
4. **Second Tier 1 API** (QR Code Generator — score 4.55, zero external dependencies)
5. Continue down the catalog by score
