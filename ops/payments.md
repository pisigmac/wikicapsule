# Payments

N/A for the open source project.

WikiCapsule is MIT-licensed and free to use. No payment processing is implemented.

## If Building SaaS

Integrate Stripe for:
- Subscription billing (monthly/annual plans)
- Usage-based metering (searches, ingests)
- Team seat management
- Invoicing for enterprise customers

**Integration points**:
- `api/webhooks/stripe.py` — webhook handlers for subscription events
- `api/billing.py` — subscription status checks
- `api/usage.py` — metered usage tracking

Recommended Stripe features:
- Stripe Checkout for plan selection
- Stripe Customer Portal for self-service management
- Stripe Webhooks for subscription lifecycle events
