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
