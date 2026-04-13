# Skills System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the complete skills directory — 22 skill files across 6 groups, plus the API catalog — that encodes all domain expertise needed to build, ship, and monetize paid APIs.

**Architecture:** Flat markdown files organized by skill group. Each file follows a consistent format (When to Consult, Principles, Patterns, Anti-Patterns, Checklist). No code — pure reference documentation. The api-catalog group includes a living catalog of 27 scored API opportunities.

**Tech Stack:** Markdown, git

---

## File Map

```
skills/
├── api-catalog/
│   ├── README.md                  # How the catalog works
│   ├── evaluation-criteria.md     # Scoring methodology
│   └── catalog.md                 # Master list of 27 API opportunities
├── api-business/
│   ├── pricing-strategies.md      # Freemium, tiered, usage-based, credits
│   ├── competitor-analysis.md     # How to evaluate incumbents
│   └── conversion-optimization.md # Free-to-paid funnel
├── shared-infra/
│   ├── architecture.md            # How the shared/ package works
│   ├── auth-and-api-keys.md       # API key issuance, validation, rotation
│   ├── usage-metering.md          # Request counting, quota enforcement
│   ├── rate-limiting.md           # Per-key, per-plan limits
│   ├── billing-stripe.md          # Stripe integration
│   └── rapidapi-compatibility.md  # Dual-channel adapter
├── api-patterns/
│   ├── data-proxy.md              # Fetch, transform, cache, serve
│   ├── ai-wrapper.md              # Wrap ML model behind clean API
│   ├── document-processor.md      # File in, result out
│   ├── generator.md               # Create artifacts (QR, PDF, etc.)
│   └── aggregator.md              # Combine multiple sources
├── fastapi-cloud/
│   ├── deployment.md              # Project structure, env vars, secrets
│   ├── scaling.md                 # Concurrency, cold starts, resources
│   └── monitoring.md              # Health checks, logging, errors
└── marketplace/
    ├── rapidapi-publishing.md     # Listing setup, tiers, docs
    ├── api-documentation.md       # OpenAPI quality, examples
    └── seo-and-discovery.md       # Naming, descriptions, tags
```

Additionally:
- Modify: `CLAUDE.md` — add Skills section

---

### Task 1: Repository scaffolding

**Files:**
- Create: `.gitignore`
- Create: `skills/` directory structure (all empty `__init__` dirs)

- [ ] **Step 1: Create .gitignore**

Create `.gitignore` at repo root:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
*.egg
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.*
!.env.example

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# mypy
.mypy_cache/

# ruff
.ruff_cache/
```

- [ ] **Step 2: Create all skill directories**

```bash
mkdir -p skills/api-catalog
mkdir -p skills/api-business
mkdir -p skills/shared-infra
mkdir -p skills/api-patterns
mkdir -p skills/fastapi-cloud
mkdir -p skills/marketplace
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```

Note: empty directories won't be tracked by git — they'll be committed as part of subsequent tasks when files are added.

---

### Task 2: API Catalog — evaluation criteria and README

**Files:**
- Create: `skills/api-catalog/README.md`
- Create: `skills/api-catalog/evaluation-criteria.md`

- [ ] **Step 1: Create catalog README**

Create `skills/api-catalog/README.md`:

```markdown
# API Catalog

The catalog is the strategic core of this project. It maintains a scored, prioritized list of API opportunities and drives the decision of what to build next.

## How It Works

1. **Identify** an API opportunity (market research, user requests, competitor gaps)
2. **Score** it using the criteria in `evaluation-criteria.md`
3. **Add** it to `catalog.md` in the appropriate tier
4. **Track** it as a GitHub issue with the `API idea` label
5. **Build** from highest score down

## Files

- `evaluation-criteria.md` — scoring methodology (demand, margin, competition, complexity)
- `catalog.md` — the master list of all API opportunities, scored and tiered

## Keeping the Catalog Current

Update `catalog.md` when:
- A new API idea is identified — add with scores to the appropriate tier
- An API ships — move to the "Shipped" section with launch date
- Market conditions change — re-score affected entries
- An API is abandoned — move to "Archived" with reason

## GitHub Issue Convention

Every catalog entry has a corresponding GitHub issue labeled `API idea`. The issue body contains the full evaluation (scores, angle, pattern). The catalog is the summary view; the issue is the detailed view.
```

- [ ] **Step 2: Create evaluation criteria skill**

Create `skills/api-catalog/evaluation-criteria.md`:

```markdown
# API Opportunity Evaluation Criteria

## When to Consult
When evaluating a new API idea, re-scoring an existing one, or deciding what to build next.

## Principles

1. Score every opportunity on four dimensions before adding to the catalog.
2. Never skip scoring — gut feel is supplementary, not primary.
3. Re-score when market conditions change (new competitor, pricing shift, demand spike).
4. A high score with low margin is worse than a medium score with high margin — margin compounds.
5. Build complexity is weighted lowest because AI handles implementation — but maintenance cost still matters.

## Scoring Dimensions

### Demand (Weight: 35%)

How many developers/businesses need this API?

| Score | Definition |
|-------|-----------|
| 5 | Universal need — every SaaS, app, or business needs this (email validation, PDF generation) |
| 4 | Broad need — most apps in several categories need this (image processing, currency conversion) |
| 3 | Category need — specific industry or use case (IBAN validation, tax lookup) |
| 2 | Niche need — small but dedicated audience (cron parsing, barcode generation) |
| 1 | Rare need — few use cases, mostly internal tooling |

**How to measure:** RapidAPI category popularity, Google Trends for "[thing] API", developer forum frequency (Stack Overflow, Reddit r/webdev), existing API call volumes on competitors.

### Margin (Weight: 25%)

Revenue per request minus cost to serve per request.

| Score | Definition |
|-------|-----------|
| 5 | Near-zero cost — pure computation, no external deps (QR codes, validation, parsing) |
| 4 | Low cost — small DB lookup or lightweight processing (geolocation, compression) |
| 3 | Moderate cost — external API calls or moderate compute (OCR, translation) |
| 2 | High cost — GPU inference, headless browser, large storage (screenshots, AI models) |
| 1 | Very high cost — real-time data feeds, premium external APIs, heavy compute |

**How to measure:** Estimate per-request cost (compute + external APIs + storage + bandwidth), compare to achievable price point.

### Competition (Weight: 25%)

How crowded is the market and how vulnerable are incumbents?

| Score | Definition |
|-------|-----------|
| 5 | No dedicated API exists — users build it themselves or use general-purpose tools |
| 4 | Few competitors, all expensive or limited — clear gap to exploit |
| 3 | Several competitors exist but with pricing gaps or quality issues |
| 2 | Well-served market with strong incumbents — need a clear differentiator |
| 1 | Dominated by free/cheap offerings — hard to monetize |

**How to measure:** RapidAPI search for category, Google "[thing] API pricing", check incumbent feature gaps and pricing tiers.

### Build Complexity (Weight: 15%)

How hard is it to build and maintain?

| Score | Definition |
|-------|-----------|
| 5 | Trivial — wrap a mature library, minimal edge cases (barcode, cron parsing) |
| 4 | Simple — well-understood problem, good libraries exist (email validation, image compression) |
| 3 | Moderate — multiple components, some integration work (PDF generation, screenshot service) |
| 2 | Complex — ML models, multiple external dependencies, state management (OCR, translation) |
| 1 | Very complex — real-time systems, complex data pipelines, compliance requirements |

**How to measure:** List dependencies, estimate number of edge cases, check if mature Python libraries exist.

## Weighted Score Calculation

```
Score = (Demand * 0.35) + (Margin * 0.25) + (Competition * 0.25) + (Complexity * 0.15)
```

## Tier Thresholds

| Tier | Score Range | Action |
|------|------------|--------|
| Tier 1 | 4.0+ | Build next — high priority |
| Tier 2 | 3.0–3.9 | Build soon — queue after Tier 1 |
| Tier 3 | < 3.0 | Backlog — revisit if conditions change |

## Anti-Patterns

- **Scoring by excitement, not data.** Every score must reference a measurable signal.
- **Ignoring maintenance cost.** A 5-complexity API that needs weekly data updates is really a 3.
- **Building Tier 2 before Tier 1 is done.** Shipping Tier 1 APIs fast generates revenue that funds Tier 2.
- **Never re-scoring.** Markets change — re-evaluate quarterly at minimum.

## Checklist

- [ ] All four dimensions scored with justification
- [ ] Score calculated using weighted formula
- [ ] Placed in correct tier
- [ ] GitHub issue created with `API idea` label
- [ ] Incumbent pricing documented
- [ ] "Our angle" clearly stated
- [ ] API pattern identified (data-proxy, generator, ai-wrapper, document-processor, aggregator)
```

- [ ] **Step 3: Commit**

```bash
git add skills/api-catalog/README.md skills/api-catalog/evaluation-criteria.md
git commit -m "feat: add API catalog README and evaluation criteria skill"
```

---

### Task 3: API Catalog — master catalog

**Files:**
- Create: `skills/api-catalog/catalog.md`

- [ ] **Step 1: Create the master catalog**

Create `skills/api-catalog/catalog.md`:

```markdown
# API Opportunity Catalog

Living document of all API opportunities, scored and tiered. See `evaluation-criteria.md` for scoring methodology.

Each entry links to its GitHub issue for full details.

---

## Tier 1 — Build Next (Score 4.0+)

### Data Proxy / Enrichment

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| Email Validation | 5 | 5 | 3 | 5 | 4.55 | #1 |
| IP Geolocation & Threat Intel | 5 | 4 | 3 | 4 | 4.15 | #2 |
| URL Metadata Extraction | 4 | 4 | 4 | 4 | 4.00 | #5 |

### Generators

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| QR Code Generator | 5 | 5 | 3 | 5 | 4.55 | #6 |
| Barcode Generation | 4 | 5 | 4 | 5 | 4.35 | #10 |
| Invoice/Receipt Generation | 4 | 5 | 4 | 4 | 4.20 | #8 |
| PDF from HTML/Templates | 5 | 4 | 3 | 4 | 4.15 | #7 |

### Document Processors

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| CSV/Excel to JSON | 4 | 5 | 4 | 5 | 4.35 | #18 |
| Image Compression & Conversion | 5 | 4 | 3 | 5 | 4.30 | #17 |
| PDF to Text/Images | 5 | 4 | 3 | 4 | 4.10 | #16 |
| Markdown to PDF/HTML | 3 | 5 | 4 | 5 | 4.05 | #19 |

### Developer Utilities

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| Cron Expression Parser | 3 | 5 | 4 | 5 | 4.00 | #22 |
| JSON Schema Validation | 3 | 5 | 4 | 5 | 4.00 | #23 |
| Placeholder Image Generation | 3 | 5 | 4 | 5 | 4.00 | #24 |

### Finance

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| IBAN / Bank Account Validation | 4 | 5 | 3 | 5 | 4.20 | #27 |

---

## Tier 2 — Build Soon (Score 3.0–3.9)

### Data Proxy / Enrichment

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| Phone Number Validation | 4 | 4 | 3 | 5 | 3.95 | #4 |
| Company/Domain Enrichment | 4 | 3 | 3 | 3 | 3.40 | #3 |

### Generators

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| Screenshot-as-a-Service | 5 | 3 | 3 | 3 | 3.70 | #9 |

### AI Wrappers

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| Sentiment Analysis | 4 | 4 | 3 | 4 | 3.80 | #14 |
| OCR / Text Extraction | 5 | 3 | 3 | 3 | 3.65 | #11 |
| Image Background Removal | 5 | 3 | 2 | 4 | 3.60 | #12 |
| Text Summarization | 4 | 2 | 3 | 4 | 3.25 | #13 |
| Language Detection & Translation | 4 | 3 | 2 | 3 | 3.05 | #15 |

### Developer Utilities

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| URL Shortener with Analytics | 4 | 5 | 2 | 5 | 3.85 | #20 |
| Webhook Relay & Inspection | 4 | 4 | 3 | 4 | 3.80 | #21 |

### Finance

| API | Demand | Margin | Competition | Complexity | Score | Issue |
|-----|--------|--------|-------------|------------|-------|-------|
| Tax Rate Lookup | 4 | 4 | 3 | 4 | 3.80 | #26 |
| Currency Conversion | 5 | 3 | 2 | 5 | 3.75 | #25 |

---

## Tier 3 — Backlog (Score < 3.0)

(Empty — all current ideas score 3.0+)

---

## Shipped

| API | Launch Date | Monthly Revenue | Notes |
|-----|------------|----------------|-------|
| (none yet) | | | |

---

## Archived

| API | Reason | Date |
|-----|--------|------|
| (none yet) | | |
```

- [ ] **Step 2: Commit**

```bash
git add skills/api-catalog/catalog.md
git commit -m "feat: add master API catalog with 27 scored opportunities"
```

---

### Task 4: API Business skills

**Files:**
- Create: `skills/api-business/pricing-strategies.md`
- Create: `skills/api-business/competitor-analysis.md`
- Create: `skills/api-business/conversion-optimization.md`

- [ ] **Step 1: Create pricing strategies skill**

Create `skills/api-business/pricing-strategies.md`:

```markdown
# Pricing Strategies for Paid APIs

## When to Consult
When setting pricing tiers for a new API, adjusting pricing for an existing one, or deciding between pricing models.

## Principles

1. **Start with usage-based pricing.** Charge per request or per unit of work. This aligns cost with value and has the lowest barrier to entry.
2. **Always offer a free tier.** 100 requests/month is the standard. It lets developers test, integrate, and build trust before paying.
3. **Three paid tiers maximum.** Basic ($9/mo, 10k req), Pro ($29/mo, 100k req), Enterprise (custom). More tiers create decision paralysis.
4. **Price based on value, not cost.** If email validation saves a customer $0.50 per bad signup avoided, charging $0.001 per validation is a steal — even if your cost is $0.0001.
5. **Overage charges, not hard cutoffs.** When a user exceeds their plan, charge per-request overage (e.g., $0.001/req) instead of blocking them. Blocked users churn; overage users upgrade.
6. **Annual discount of 20%.** Offer it but don't push it — monthly flexibility is what API customers want.
7. **RapidAPI and direct pricing must match.** If your Pro tier is $29/mo on RapidAPI, it's $29/mo direct. Users will find the discrepancy and feel cheated.

## Patterns

### Standard Tier Template

| Tier | Requests/Month | Price | Overage |
|------|---------------|-------|---------|
| Free | 100 | $0 | Hard cutoff |
| Basic | 10,000 | $9/mo | $0.002/req |
| Pro | 100,000 | $29/mo | $0.001/req |
| Enterprise | Custom | Custom | Custom |

### Adjustments by API Type

- **High-compute APIs** (screenshots, OCR, background removal): halve the request limits or double the price.
- **Near-zero-cost APIs** (validation, parsing, QR codes): keep the template as-is — volume is the play.
- **Data-dependent APIs** (geolocation, enrichment): add a data freshness tier — real-time costs more than cached.

### Credit-Based Alternative

For APIs where requests vary wildly in cost (e.g., PDF generation — 1 page vs. 100 pages):

| Tier | Credits/Month | Price | Credit Cost |
|------|-------------- |-------|-------------|
| Free | 100 | $0 | 1 credit = 1 page |
| Basic | 5,000 | $9/mo | |
| Pro | 50,000 | $29/mo | |

## Anti-Patterns

- **No free tier.** Developers won't integrate an API they can't test. Zero free tier = zero adoption.
- **Pricing too high at launch.** Start low, prove value, raise prices for new subscribers. Existing subscribers keep their rate (grandfather clause).
- **Complex per-feature pricing.** "Basic gets endpoints A and B, Pro adds C and D" — this is confusing. All tiers get all endpoints; only the request volume changes.
- **Hiding pricing.** If users can't find your pricing in 10 seconds, they leave. Put it on the landing page and in the API docs.

## Checklist

- [ ] Free tier offers enough requests to test and integrate (minimum 100/mo)
- [ ] No more than 3 paid tiers
- [ ] Overage pricing set (not hard cutoff for paid tiers)
- [ ] RapidAPI and direct pricing match
- [ ] Price reflects value to customer, not just cost to serve
- [ ] Per-API adjustment applied if compute cost is above average
```

- [ ] **Step 2: Create competitor analysis skill**

Create `skills/api-business/competitor-analysis.md`:

```markdown
# Competitor Analysis for API Opportunities

## When to Consult
When evaluating a new API idea, writing the "Our Angle" section for a catalog entry, or deciding how to differentiate.

## Principles

1. **Find the incumbent's pricing page first.** The pricing page tells you the market rate, the feature gates, and the pain points (look at what's locked behind expensive tiers).
2. **Check RapidAPI for the category.** Sort by popularity. The top 3 APIs tell you what users want. Their reviews tell you what users hate.
3. **Look for the "Typeform problem."** A good product that's overpriced for what it does. The uform playbook: same core features, 5-10x cheaper, API-first.
4. **Identify the lock-in mechanism.** Why do users stay with the incumbent? Switching cost? Data portability? API compatibility? If lock-in is low, you can steal users with price alone.
5. **Never compete on features against a well-funded incumbent.** Compete on price, simplicity, or developer experience. You will not out-feature Twilio.

## Patterns

### Competitor Evaluation Template

For each competitor, document:

```
### [Competitor Name]
- **URL:** [pricing page URL]
- **Free tier:** [what's included]
- **Cheapest paid tier:** [price and limits]
- **Most popular tier:** [price and limits, if known]
- **API quality:** [good/mediocre/poor — check their docs]
- **Pain points:** [from reviews, forums, social media]
- **Lock-in level:** [high/medium/low]
- **Our advantage:** [specific — price, speed, simplicity, bundling]
```

### Where to Find Competitor Intelligence

1. **RapidAPI** — search the category, read reviews, check popularity rankings
2. **G2/Capterra** — enterprise-focused reviews, useful for understanding pain points
3. **Reddit r/webdev, r/SaaS** — developers complaining about pricing or limitations
4. **Stack Overflow** — questions about alternatives signal unmet demand
5. **Product Hunt** — launches and comments reveal positioning and reception
6. **Twitter/X** — search "[competitor] pricing" or "[competitor] alternative"

### Pricing Gap Analysis

```
Incumbent price per unit: $X
Our cost per unit: $Y
Our price per unit: $Z (where Y < Z < X, typically Z = X/5 to X/10)
Margin per unit: $Z - $Y
```

If you can't achieve at least 50% margin while being 3x cheaper than the incumbent, the opportunity is weak.

## Anti-Patterns

- **Assuming no competition means a good opportunity.** No competition often means no demand. Check demand signals independently.
- **Competing on features with Big Tech APIs.** Google, AWS, and Azure have infinite engineering resources. Compete on simplicity and price.
- **Ignoring free open-source alternatives.** If a mature, easy-to-use library exists (e.g., qrcode for QR generation), your API must add value beyond "hosted version" — styling, speed, no-dependency integration.
- **Copying competitor pricing exactly.** Undercut by 3-10x, not 10%. Small discounts don't motivate switching.

## Checklist

- [ ] At least 3 competitors evaluated (or documented that fewer exist)
- [ ] Incumbent pricing page URL recorded
- [ ] Pain points identified from reviews/forums
- [ ] Pricing gap calculated with target margin
- [ ] "Our Angle" clearly states why users switch
- [ ] Lock-in level assessed — low lock-in = easier steal
```

- [ ] **Step 3: Create conversion optimization skill**

Create `skills/api-business/conversion-optimization.md`:

```markdown
# Conversion Optimization for Paid APIs

## When to Consult
When designing the free-to-paid funnel, onboarding flow, or when conversion rates are below expectations.

## Principles

1. **Time-to-first-successful-call must be under 5 minutes.** Sign up, get API key, make a request, see a result. Every friction point between these steps loses users.
2. **The free tier is the funnel, not the product.** Its only purpose is to get developers to integrate. Once integrated, upgrading is easy; ripping out is hard.
3. **Usage emails beat marketing emails.** "You've used 80 of your 100 free requests this month" converts better than "Upgrade now for 50% off."
4. **Show the cost of NOT upgrading.** "Your app returned 47 errors this month because of quota limits" is more motivating than "Get 10,000 requests for $9."
5. **API keys are the lock-in.** Once a key is hardcoded in production, switching APIs is a code change + deployment. Make getting the key frictionless.
6. **Developers are the buyers.** They decide which APIs to integrate. Speak their language: code examples, curl commands, SDKs. Not marketing slides.

## Patterns

### Onboarding Funnel

```
1. Landing page with live demo (try the API without signing up)
   ↓
2. Sign up (email + password, or GitHub OAuth)
   ↓
3. API key generated immediately (shown on dashboard, copied to clipboard)
   ↓
4. Getting started page with curl example using THEIR key
   ↓
5. First successful API call
   ↓
6. Integration in their app
   ↓
7. Hit free tier limit
   ↓
8. Usage alert email → upgrade page
```

### Sticky API Patterns

APIs that are hardest to replace (highest retention):

- **Data enrichment** — integrated into signup/onboarding flows, called on every new user
- **Document generation** — invoices, PDFs, reports tied to business-critical workflows
- **Validation** — email, phone, IBAN checks baked into form submissions
- **Image processing** — e-commerce product pipelines depend on it

APIs that are easiest to replace (lowest retention):

- **One-off utilities** — URL shortener, QR code (can be swapped trivially)
- **Commodity data** — currency rates, weather (identical output from any provider)

### Usage Alert Email Template

```
Subject: You've used 80% of your free API quota

Hi {name},

Your {api_name} usage this month: {used}/{limit} requests.

At your current rate, you'll hit your limit in {days_remaining} days.

Upgrade to Basic ($9/mo) for 10,000 requests:
{upgrade_url}

— {api_name} Team
```

## Anti-Patterns

- **Requiring credit card for free tier.** Kills signups. Free tier = zero commitment.
- **Slow API key generation.** "We'll email you your key within 24 hours" — developer is gone in 24 seconds.
- **No code examples.** A pricing page without a curl command is a bounced developer.
- **Blocking free tier users hard.** Return 402 with an upgrade URL in the response body, not a generic 403.

## Checklist

- [ ] Sign up to API key in under 2 minutes
- [ ] Getting started guide with copy-paste curl command
- [ ] At least 3 code examples (curl, Python, JavaScript)
- [ ] Usage alerts configured at 50%, 80%, 100% of quota
- [ ] 402 response includes upgrade URL for over-quota requests
- [ ] Free tier generous enough to complete integration (minimum 100 requests)
```

- [ ] **Step 4: Commit**

```bash
git add skills/api-business/
git commit -m "feat: add API business skills — pricing, competitor analysis, conversion"
```

---

### Task 5: Shared Infrastructure skills

**Files:**
- Create: `skills/shared-infra/architecture.md`
- Create: `skills/shared-infra/auth-and-api-keys.md`
- Create: `skills/shared-infra/usage-metering.md`
- Create: `skills/shared-infra/rate-limiting.md`
- Create: `skills/shared-infra/billing-stripe.md`
- Create: `skills/shared-infra/rapidapi-compatibility.md`

- [ ] **Step 1: Create architecture skill**

Create `skills/shared-infra/architecture.md`:

```markdown
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
```

- [ ] **Step 2: Create auth and API keys skill**

Create `skills/shared-infra/auth-and-api-keys.md`:

```markdown
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
```

- [ ] **Step 3: Create usage metering skill**

Create `skills/shared-infra/usage-metering.md`:

```markdown
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
```

- [ ] **Step 4: Create rate limiting skill**

Create `skills/shared-infra/rate-limiting.md`:

```markdown
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
```

- [ ] **Step 5: Create billing Stripe skill**

Create `skills/shared-infra/billing-stripe.md`:

```markdown
# Billing with Stripe

## When to Consult
When implementing Stripe integration, handling subscription changes, or debugging billing issues.

## Principles

1. **Stripe is the billing system of record for direct customers.** RapidAPI handles its own billing. Stripe only applies to users who sign up directly.
2. **Usage-based billing via Stripe Metered Billing.** Report usage to Stripe, Stripe generates invoices. Don't build a custom invoicing system.
3. **Webhook-driven state management.** Never poll Stripe. React to webhooks: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`.
4. **Plan changes take effect immediately.** When a user upgrades, update their plan in PostgreSQL immediately. Stripe prorates automatically.
5. **Failed payments get a 7-day grace period.** Don't downgrade instantly on payment failure. Send reminders at day 1, 3, 5. Downgrade to free on day 7.

## Patterns

### Stripe Product/Price Structure

```
Product: "Email Validator API"
  ├── Price: "Basic" — $9/mo, metered (up to 10k requests included)
  ├── Price: "Pro" — $29/mo, metered (up to 100k requests included)
  └── Price: "Enterprise" — custom

Product: "QR Code Generator API"
  ├── Price: "Basic" — $9/mo, metered
  ├── Price: "Pro" — $29/mo, metered
  └── Price: "Enterprise" — custom
```

Each API is a separate Stripe Product. Each tier is a Price on that Product.

### Webhook Events to Handle

| Event | Action |
|-------|--------|
| `customer.subscription.created` | Create/update user plan in PostgreSQL |
| `customer.subscription.updated` | Update plan limits, handle up/downgrades |
| `customer.subscription.deleted` | Downgrade to free tier |
| `invoice.payment_succeeded` | Update billing status, clear any warnings |
| `invoice.payment_failed` | Start grace period, send reminder email |
| `customer.subscription.trial_will_end` | Send conversion email (if using trials) |

### Webhook Security

```python
import stripe

def verify_webhook(payload: bytes, sig_header: str, webhook_secret: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
```

Always verify the webhook signature. Never trust the payload without verification.

### Usage Reporting to Stripe

At the end of each billing period (or on-demand via background task):

```python
stripe.SubscriptionItem.create_usage_record(
    subscription_item_id,
    quantity=usage_count,
    timestamp=period_end,
    action="set",  # absolute count, not increment
)
```

## Anti-Patterns

- **Building custom invoicing.** Stripe handles invoices, receipts, tax calculation, and payment retries. Don't reinvent this.
- **Polling Stripe for subscription status.** Webhooks push changes to you in real-time. Polling adds latency and API call costs.
- **Instant downgrade on payment failure.** Users may have a temporary card issue. Grace period prevents unnecessary churn.
- **Storing full card details.** Stripe handles PCI compliance. Never touch card numbers. Use Stripe Checkout or Elements.

## Checklist

- [ ] Each API is a separate Stripe Product
- [ ] Each tier is a separate Stripe Price (metered billing)
- [ ] Webhook endpoint verifies Stripe signatures
- [ ] All 6 webhook events handled (see table above)
- [ ] 7-day grace period for failed payments
- [ ] Usage reported to Stripe via usage records
- [ ] Stripe secret key and webhook secret in environment variables (never hardcoded)
```

- [ ] **Step 6: Create RapidAPI compatibility skill**

Create `skills/shared-infra/rapidapi-compatibility.md`:

```markdown
# RapidAPI Compatibility

## When to Consult
When adding RapidAPI support to a new API, debugging RapidAPI-specific issues, or handling dual-channel logic.

## Principles

1. **RapidAPI is a proxy.** Requests come from RapidAPI's servers, not the end user. The real user identity is in `X-RapidAPI-User`.
2. **Validate the proxy secret on every request.** `X-RapidAPI-Proxy-Secret` must match your configured secret. Without this check, anyone can spoof RapidAPI headers.
3. **RapidAPI handles billing for its channel.** Don't charge RapidAPI users via Stripe. Meter their usage for analytics only.
4. **The API must behave identically regardless of channel.** Same endpoints, same response format, same rate limits. The only difference is how auth works.
5. **RapidAPI adds latency.** One extra network hop. Don't add more by doing redundant auth checks.

## Patterns

### Channel Detection

```python
from starlette.requests import Request

def detect_channel(request: Request) -> str:
    if request.headers.get("X-RapidAPI-Proxy-Secret"):
        return "rapidapi"
    return "direct"
```

Store the channel in `request.state.channel` via middleware. Downstream code checks `request.state.channel` when behavior differs.

### RapidAPI Headers

| Header | Purpose |
|--------|---------|
| `X-RapidAPI-Proxy-Secret` | Authenticates that the request came from RapidAPI (not spoofed) |
| `X-RapidAPI-User` | The RapidAPI subscriber's username |
| `X-RapidAPI-Subscription` | The subscriber's plan tier on RapidAPI |

### Dual-Channel Auth Dependency

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, Request

async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(None),
    x_rapidapi_proxy_secret: str | None = Header(None),
) -> AuthContext:
    if x_rapidapi_proxy_secret:
        # RapidAPI channel
        if x_rapidapi_proxy_secret != settings.rapidapi_proxy_secret:
            raise HTTPException(status_code=401, detail="Invalid proxy secret")
        return AuthContext(
            channel="rapidapi",
            user_id=request.headers.get("X-RapidAPI-User", "unknown"),
            plan=request.headers.get("X-RapidAPI-Subscription", "free"),
        )
    elif x_api_key:
        # Direct channel — validate API key against database
        key_record = await validate_api_key(x_api_key)
        return AuthContext(
            channel="direct",
            user_id=key_record.user_id,
            plan=key_record.plan_id,
        )
    else:
        raise HTTPException(status_code=401, detail="API key required")
```

### Testing RapidAPI Locally

Include the RapidAPI headers in test requests:

```bash
curl -H "X-RapidAPI-Proxy-Secret: test-secret" \
     -H "X-RapidAPI-User: test-user" \
     -H "X-RapidAPI-Subscription: BASIC" \
     http://localhost:8000/validate?email=test@example.com
```

## Anti-Patterns

- **Skipping proxy secret validation.** Anyone can send `X-RapidAPI-User: premium-user` headers. Without proxy secret validation, your API is open to abuse.
- **Different response formats per channel.** The consumer's code shouldn't need to know which channel it came through.
- **Billing RapidAPI users via Stripe.** Double billing. RapidAPI already charged them.
- **Ignoring `X-RapidAPI-Subscription` for rate limiting.** Use it to apply plan-appropriate rate limits, even though RapidAPI has its own limits.

## Checklist

- [ ] `X-RapidAPI-Proxy-Secret` validated on every RapidAPI request
- [ ] `X-RapidAPI-User` extracted and stored in request state
- [ ] Channel detection sets `request.state.channel`
- [ ] Same response format regardless of channel
- [ ] Metering applies to both channels
- [ ] Billing only applies to direct channel
- [ ] Proxy secret stored in environment variable
```

- [ ] **Step 7: Commit**

```bash
git add skills/shared-infra/
git commit -m "feat: add shared infrastructure skills — auth, metering, rate limiting, billing, RapidAPI"
```

---

### Task 6: API Pattern skills

**Files:**
- Create: `skills/api-patterns/data-proxy.md`
- Create: `skills/api-patterns/ai-wrapper.md`
- Create: `skills/api-patterns/document-processor.md`
- Create: `skills/api-patterns/generator.md`
- Create: `skills/api-patterns/aggregator.md`

- [ ] **Step 1: Create data proxy pattern skill**

Create `skills/api-patterns/data-proxy.md`:

```markdown
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
```

- [ ] **Step 2: Create AI wrapper pattern skill**

Create `skills/api-patterns/ai-wrapper.md`:

```markdown
# AI Wrapper Pattern

## When to Consult
When building an API that wraps a machine learning model or external AI service. Examples: OCR, background removal, sentiment analysis, summarization, translation.

## Principles

1. **Pick the right model tier.** Open-source models (Tesseract, rembg, VADER) for cost-sensitive APIs. External AI APIs (OpenAI, Claude) for quality-sensitive APIs. Never use an expensive model where a cheap one suffices.
2. **Async processing for heavy inference.** If inference takes > 2 seconds, return a job ID and let the client poll or use a webhook callback.
3. **Input size limits are non-negotiable.** Unbounded input (a 500MB image, a 100-page PDF) will crash your server or blow your costs. Set limits per plan.
4. **Model versioning matters.** When you upgrade a model, old responses may differ. Version your model in the response metadata so users know what generated the result.
5. **Fallback chain for reliability.** Primary model → fallback model → graceful error. Example: custom OCR model → Tesseract fallback → "unable to extract text."

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── process.py         # Accepts input, returns result
│   ├── schemas/
│   │   ├── request.py         # Input constraints (max size, format)
│   │   └── response.py        # Result + metadata (model version, confidence)
│   ├── services/
│   │   ├── model.py           # Model loading and inference
│   │   └── preprocessor.py    # Input normalization
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Response Schema

```python
class AIResponse(BaseModel):
    result: ResultModel
    model_version: str      # e.g., "tesseract-5.3.1" or "rembg-2.0.50"
    confidence: float | None  # 0.0-1.0 if applicable
    processing_time_ms: int
```

### Sync vs Async Decision

```
Inference time < 2s  →  Synchronous response
Inference time 2-30s →  Return job_id, poll endpoint
Inference time > 30s →  Return job_id, webhook callback
```

### File Upload Handling

```python
from fastapi import UploadFile

@router.post("/process")
async def process_file(
    file: UploadFile,
    auth: AuthContext = Depends(require_api_key),
) -> AIResponse:
    if file.size and file.size > settings.max_file_size:
        raise AppException(413, "File too large", "file_too_large")
    content = await file.read()
    result = await model_service.process(content)
    return AIResponse(result=result, ...)
```

## Anti-Patterns

- **Loading the model on every request.** Load once at startup (lifespan), reuse across requests. Model loading takes seconds; inference takes milliseconds.
- **No input size limits.** A 1GB upload will OOM your server. Enforce limits at the route level.
- **Blocking the event loop with CPU-bound inference.** Use `asyncio.to_thread()` or a process pool for CPU-heavy model inference.
- **No confidence scores.** If the model supports it, always return confidence. Users want to filter low-confidence results.

## Checklist

- [ ] Model loaded once at startup, not per request
- [ ] Input size limits enforced per plan
- [ ] CPU-bound inference runs in thread/process pool
- [ ] Response includes model_version and processing_time_ms
- [ ] Confidence score included when model supports it
- [ ] File upload uses FastAPI's UploadFile (streaming, not loading full body into memory)
```

- [ ] **Step 3: Create document processor pattern skill**

Create `skills/api-patterns/document-processor.md`:

```markdown
# Document Processor Pattern

## When to Consult
When building an API that accepts a document (PDF, image, spreadsheet) and extracts or transforms its content. Examples: PDF to text, image compression, CSV to JSON, format conversion.

## Principles

1. **File in, result out.** Accept a file upload, process it, return the result. Simple contract.
2. **Support both file upload and URL input.** Some users have files locally; others have them at a URL. Support both.
3. **Stream large outputs.** If the result is a large file (e.g., compressed image, generated PDF), use `StreamingResponse` to avoid holding the full result in memory.
4. **Validate file type and size before processing.** Check MIME type and magic bytes, not just the file extension. Reject early and fast.
5. **Temporary file cleanup is mandatory.** Use `tempfile` with context managers. Never leave temp files on disk after the request completes.

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── convert.py         # or extract.py, compress.py
│   ├── schemas/
│   │   ├── request.py         # Input options (format, quality, pages)
│   │   └── response.py        # Result metadata
│   ├── services/
│   │   ├── processor.py       # Core processing logic
│   │   └── file_handler.py    # File validation, temp file management
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Dual Input (file upload + URL)

```python
from fastapi import File, UploadFile

@router.post("/convert")
async def convert(
    file: UploadFile | None = File(None),
    url: str | None = None,
) -> StreamingResponse:
    if file and url:
        raise AppException(400, "Provide file or URL, not both", "invalid_input")
    if not file and not url:
        raise AppException(400, "Provide file or URL", "missing_input")

    if url:
        content = await fetch_url(url)
    else:
        content = await file.read()

    result = await processor.convert(content)
    return StreamingResponse(result, media_type="application/pdf")
```

### File Validation

```python
import magic

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}

def validate_file(content: bytes, max_size: int) -> str:
    if len(content) > max_size:
        raise AppException(413, "File too large", "file_too_large")
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_TYPES:
        raise AppException(415, f"Unsupported file type: {mime_type}", "unsupported_type")
    return mime_type
```

### Temp File Context Manager

```python
import tempfile
from pathlib import Path

async def process_with_tempfile(content: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        result = await do_processing(Path(tmp.name))
        return result
```

## Anti-Patterns

- **Trusting file extensions.** A `.pdf` extension doesn't mean it's a PDF. Validate with magic bytes.
- **Holding entire output in memory.** A 100-page PDF-to-image conversion can generate gigabytes. Stream the output.
- **No file size limits.** Without limits, a single request can exhaust server memory.
- **Leaving temp files on disk.** Use `tempfile` with `delete=True` or explicit cleanup in a `finally` block.

## Checklist

- [ ] Both file upload and URL input supported
- [ ] File type validated via magic bytes, not extension
- [ ] File size limit enforced before processing
- [ ] Large outputs use StreamingResponse
- [ ] Temp files cleaned up after request completes
- [ ] Processing runs in thread pool if CPU-bound
```

- [ ] **Step 4: Create generator pattern skill**

Create `skills/api-patterns/generator.md`:

```markdown
# Generator Pattern

## When to Consult
When building an API that creates artifacts from parameters. Examples: QR codes, barcodes, PDFs, invoices, placeholder images, screenshots.

## Principles

1. **Input is parameters, output is a file.** The consumer sends JSON options (text, colors, size), the API returns an image/PDF/file.
2. **Support multiple output formats.** QR code API should support PNG, SVG, and PDF. Let the consumer choose via query parameter or Accept header.
3. **Sensible defaults for everything.** A QR code request with just `data=hello` should return a usable image. Colors, size, format should all have defaults.
4. **Cache generated artifacts.** The same parameters produce the same output. Cache by hashing the input parameters. Saves CPU for repeat requests.
5. **Return the file directly, not a URL.** For small artifacts (QR codes, barcodes), return the binary data with the correct Content-Type. No extra round-trip.

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── generate.py        # Accepts parameters, returns artifact
│   ├── schemas/
│   │   └── request.py         # Generation options with defaults
│   ├── services/
│   │   └── generator.py       # Core generation logic
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Request Schema with Defaults

```python
class GenerateRequest(BaseModel):
    data: str                              # Required
    format: Literal["png", "svg", "pdf"] = "png"
    size: int = Field(default=300, ge=50, le=2000)
    foreground_color: str = "#000000"
    background_color: str = "#FFFFFF"
```

### Binary Response

```python
@router.post("/generate", response_class=Response)
async def generate(params: GenerateRequest) -> Response:
    content = await generator.create(params)
    media_types = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}
    return Response(
        content=content,
        media_type=media_types[params.format],
        headers={"Content-Disposition": f"inline; filename=output.{params.format}"},
    )
```

### Input-Based Caching

```python
import hashlib
import json

def cache_key(params: GenerateRequest) -> str:
    param_str = json.dumps(params.model_dump(), sort_keys=True)
    return f"gen:{hashlib.sha256(param_str.encode()).hexdigest()}"
```

## Anti-Patterns

- **Returning a URL instead of the file.** For artifacts under 1MB, return the binary directly. URLs add latency and require storage management.
- **No format options.** SVG is better for web, PNG for apps, PDF for print. Support all three when feasible.
- **Ignoring Content-Disposition header.** Without it, browsers don't know the filename. Use `inline` for display, `attachment` for download.
- **No input validation on size/dimensions.** A 50,000x50,000 pixel image request will OOM the server. Set max dimensions.

## Checklist

- [ ] Multiple output formats supported
- [ ] Sensible defaults for all optional parameters
- [ ] Input validation with min/max bounds on dimensions
- [ ] Binary response with correct Content-Type
- [ ] Content-Disposition header set
- [ ] Repeat requests cached by input hash
- [ ] Max output size enforced
```

- [ ] **Step 5: Create aggregator pattern skill**

Create `skills/api-patterns/aggregator.md`:

```markdown
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
```

- [ ] **Step 6: Commit**

```bash
git add skills/api-patterns/
git commit -m "feat: add API pattern skills — data proxy, AI wrapper, document processor, generator, aggregator"
```

---

### Task 7: FastAPI Cloud skills

**Files:**
- Create: `skills/fastapi-cloud/deployment.md`
- Create: `skills/fastapi-cloud/scaling.md`
- Create: `skills/fastapi-cloud/monitoring.md`

- [ ] **Step 1: Create deployment skill**

Create `skills/fastapi-cloud/deployment.md`:

```markdown
# FastAPI Cloud Deployment

## When to Consult
When deploying a new API project to FastAPI Cloud, configuring environment variables, or troubleshooting deployment issues.

## Principles

1. **One FastAPI Cloud app per project.** Each project in `projects/` deploys independently. They share the shared infra package but are separate deployments.
2. **FastAPI Cloud auto-discovers the app.** It looks for a `FastAPI()` instance in `main.py`. No special configuration needed.
3. **Environment variables for all configuration.** Database URLs, Redis URLs, Stripe keys, RapidAPI secrets — all injected via FastAPI Cloud dashboard, consumed via Pydantic Settings.
4. **The `shared/` package ships with each project.** It's a path dependency in `pyproject.toml`. FastAPI Cloud installs it as part of the project's dependencies.
5. **Never commit secrets.** Use `.env.example` to document required variables. `.env` is in `.gitignore`.

## Patterns

### Project pyproject.toml

```toml
[project]
name = "email-validator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]",
    "pydantic-settings",
    "httpx",
    "shared @ file://../../shared",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
strict = true
python_version = "3.12"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### .env.example

```env
# Injected by FastAPI Cloud
APP_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
APP_REDIS_URL=redis://host:6379/0

# Configure in FastAPI Cloud dashboard
APP_STRIPE_SECRET_KEY=sk_test_...
APP_STRIPE_WEBHOOK_SECRET=whsec_...
APP_RAPIDAPI_PROXY_SECRET=your-proxy-secret

# Project-specific
APP_PROJECT_NAME=email-validator
```

### Config Pattern

```python
from functools import cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: str
    redis_url: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    rapidapi_proxy_secret: str
    project_name: str

@cache
def get_settings() -> Settings:
    return Settings()
```

## Anti-Patterns

- **Hardcoding connection strings.** Even for development. Use `.env` files locally, FastAPI Cloud dashboard in production.
- **Multiple FastAPI apps in one deployment.** Each project deploys separately. Don't try to serve multiple APIs from one app.
- **Committing `.env` files.** `.env` is in `.gitignore`. Only `.env.example` (with placeholder values) is committed.
- **Installing shared as a git submodule.** Path dependency is simpler and faster. `shared @ file://../../shared` works locally and on FastAPI Cloud.

## Checklist

- [ ] `pyproject.toml` includes `shared` as path dependency
- [ ] `.env.example` documents all required environment variables
- [ ] `.env` is in `.gitignore`
- [ ] Pydantic Settings class uses `env_prefix="APP_"`
- [ ] Settings loaded via `@cache`-decorated function
- [ ] `main.py` has a `FastAPI()` instance at module level
```

- [ ] **Step 2: Create scaling skill**

Create `skills/fastapi-cloud/scaling.md`:

```markdown
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
```

- [ ] **Step 3: Create monitoring skill**

Create `skills/fastapi-cloud/monitoring.md`:

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add skills/fastapi-cloud/
git commit -m "feat: add FastAPI Cloud skills — deployment, scaling, monitoring"
```

---

### Task 8: Marketplace skills

**Files:**
- Create: `skills/marketplace/rapidapi-publishing.md`
- Create: `skills/marketplace/api-documentation.md`
- Create: `skills/marketplace/seo-and-discovery.md`

- [ ] **Step 1: Create RapidAPI publishing skill**

Create `skills/marketplace/rapidapi-publishing.md`:

```markdown
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
```

- [ ] **Step 2: Create API documentation skill**

Create `skills/marketplace/api-documentation.md`:

```markdown
# API Documentation Standards

## When to Consult
When writing endpoint documentation, creating examples, or improving the developer experience of an API.

## Principles

1. **FastAPI generates the docs.** Use docstrings, `summary`, `description`, `response_model`, and `responses` parameters on route decorators. The OpenAPI spec is the single source of truth.
2. **Every endpoint needs at least 3 examples.** A minimal request, a fully-specified request, and an error case. Use FastAPI's `openapi_examples` parameter.
3. **Error responses must be documented.** Use the `responses` parameter to document all possible error status codes with example response bodies.
4. **Schema descriptions on every field.** Use Pydantic `Field(description="...")` on every field. These appear in the auto-generated docs.

## Patterns

### Route with Full Documentation

```python
@router.post(
    "/validate",
    summary="Validate an email address",
    description="Checks syntax, MX records, SMTP reachability, and disposable email detection.",
    response_model=ValidationResponse,
    responses={
        400: {"description": "Invalid email format", "model": ErrorResponse},
        429: {"description": "Rate limit or quota exceeded", "model": ErrorResponse},
    },
)
async def validate_email(request: ValidationRequest) -> ValidationResponse:
    ...
```

### Pydantic Schema with Descriptions

```python
class ValidationRequest(BaseModel):
    email: str = Field(
        description="Email address to validate",
        examples=["user@example.com"],
    )
    check_smtp: bool = Field(
        default=True,
        description="Whether to verify the mailbox exists via SMTP",
    )

class ValidationResponse(BaseModel):
    email: str = Field(description="The email address that was validated")
    is_valid: bool = Field(description="Overall validation result")
    checks: CheckResults = Field(description="Detailed results for each check")
```

### OpenAPI Examples

```python
@router.post(
    "/validate",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "minimal": {
                            "summary": "Minimal request",
                            "value": {"email": "user@example.com"},
                        },
                        "full": {
                            "summary": "Full request with options",
                            "value": {"email": "user@example.com", "check_smtp": True},
                        },
                    }
                }
            }
        }
    },
)
```

## Anti-Patterns

- **No descriptions on schema fields.** `email: str` tells the developer nothing about format expectations. Add `Field(description=...)`.
- **Only documenting happy path.** Error responses are more important than success responses — developers need to know what can go wrong.
- **Writing docs in a separate file.** Docs belong in the code (docstrings, Field descriptions, route parameters). Separate docs get out of sync.
- **Using generic examples.** `"string"`, `"example@example.com"` — use realistic data like `"alice.smith@company.com"`.

## Checklist

- [ ] Every route has `summary` and `description`
- [ ] Every Pydantic field has `description` and `examples`
- [ ] Error responses documented with `responses` parameter
- [ ] At least 3 OpenAPI examples per endpoint
- [ ] `/docs` (Swagger UI) loads and all endpoints are testable
- [ ] Error response includes `error` code and `detail` message
```

- [ ] **Step 3: Create SEO and discovery skill**

Create `skills/marketplace/seo-and-discovery.md`:

```markdown
# SEO and Discovery for API Marketplace

## When to Consult
When naming an API, writing its description, choosing tags, or optimizing for marketplace search rankings.

## Principles

1. **Name the API after what it does.** "Email Validation API" ranks for "email validation API" searches. "SmartMail Pro" ranks for nothing.
2. **Front-load keywords in the description.** The first 160 characters appear in search results. Put the most important keywords there.
3. **Tags match user search terms.** Users search "email verify", "validate email", "check email", "email checker" — add all variations as tags.
4. **Category placement matters.** RapidAPI organizes by category. Choose the most specific category that fits. "Email" > "Data" > "Tools".
5. **Pricing visibility drives clicks.** Listings showing "Freemium" get more clicks than "Paid". Always have a free tier.

## Patterns

### API Naming Convention

```
[Action] [Object] API

Examples:
  Email Validation API
  QR Code Generator API
  PDF to Text API
  Image Compression API
  Currency Conversion API
```

- Use the most common search term for the object (not a brand name)
- Include "API" in the name — users search for "[thing] API"
- Keep it under 40 characters

### Description Structure (First 160 chars)

```
Validate email addresses with MX record lookup, SMTP verification, and disposable email detection. Fast, accurate, and affordable.
```

- What it does (validate email addresses)
- How it does it (MX, SMTP, disposable detection)
- Why choose this one (fast, accurate, affordable)

### Tag Strategy

For "Email Validation API":
```
email validation, email verification, email checker, validate email,
verify email, MX record, SMTP check, disposable email, email API,
bulk email validation
```

- Include the exact API name
- Include synonyms (validation/verification/checker)
- Include technical terms (MX record, SMTP)
- Include use-case terms (bulk email validation)
- 10-15 tags per API

### Long Description Template

```markdown
# Email Validation API

Validate email addresses in real-time with comprehensive checks:

## Checks Performed
- **Syntax validation** — RFC 5322 compliance
- **MX record lookup** — verify the domain accepts email
- **SMTP verification** — check if the mailbox exists
- **Disposable email detection** — block temporary email services
- **Role-based detection** — identify addresses like info@, admin@

## Why Choose This API?
- **Fast** — average response time under 200ms
- **Accurate** — 99.5%+ accuracy on deliverability prediction
- **Affordable** — free tier included, paid plans start at $9/mo
- **Simple** — one endpoint, one request, one response

## Getting Started
1. Subscribe to the free plan
2. Make a POST request to /validate with your email
3. Get instant validation results

## Pricing
- Free: 100 requests/month
- Basic: 10,000 requests/month ($9/mo)
- Pro: 100,000 requests/month ($29/mo)
```

## Anti-Patterns

- **Brand-name API titles.** "VeriMailX" is meaningless in search results. Use descriptive names.
- **Empty or generic descriptions.** "A powerful email API" competes with nothing and ranks for nothing.
- **Too few tags.** Use all available tag slots. More tags = more search surface.
- **Wrong category.** An email validation API in the "Machine Learning" category won't be found by the right audience.

## Checklist

- [ ] API name follows "[Action] [Object] API" format
- [ ] First 160 chars of description contain primary keywords
- [ ] 10-15 tags including synonyms and technical terms
- [ ] Most specific RapidAPI category selected
- [ ] Long description includes features, use cases, getting started, and pricing
- [ ] Free tier shown in pricing (displays "Freemium" badge)
```

- [ ] **Step 4: Commit**

```bash
git add skills/marketplace/
git commit -m "feat: add marketplace skills — RapidAPI publishing, documentation, SEO"
```

---

### Task 9: Update CLAUDE.md with Skills section

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add Skills section to CLAUDE.md**

Add the following section after the "Keeping This File Up to Date" section (before "GitHub Issues as Source of Truth"):

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

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Skills section to CLAUDE.md"
```

---

## Summary

| Task | Files | Description |
|------|-------|-------------|
| 1 | 1 | .gitignore + directory structure |
| 2 | 2 | API catalog README + evaluation criteria |
| 3 | 1 | Master catalog (27 APIs scored and tiered) |
| 4 | 3 | API business skills (pricing, competitors, conversion) |
| 5 | 6 | Shared infra skills (auth, metering, rate limiting, billing, RapidAPI) |
| 6 | 5 | API pattern skills (data proxy, AI wrapper, doc processor, generator, aggregator) |
| 7 | 3 | FastAPI Cloud skills (deployment, scaling, monitoring) |
| 8 | 3 | Marketplace skills (RapidAPI publishing, docs, SEO) |
| 9 | 1 | CLAUDE.md update |
| **Total** | **25 files** | **9 tasks, ~9 commits** |
