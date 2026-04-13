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
