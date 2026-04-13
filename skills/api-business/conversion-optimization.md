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
