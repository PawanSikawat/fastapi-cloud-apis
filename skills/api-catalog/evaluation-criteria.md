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
