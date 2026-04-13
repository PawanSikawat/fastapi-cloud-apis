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
