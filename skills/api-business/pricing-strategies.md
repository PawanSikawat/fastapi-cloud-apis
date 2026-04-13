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
