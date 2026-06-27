# Pricing

## Open Source

WikiCapsule is open source under the MIT License. The full feature set is free.

```
MIT License

Copyright (c) 2024 WikiCapsule Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## Self-Hosted (Free)

Everything. All features, all tools, all integrations. Run it on your machine, your server, your cloud. No restrictions.

## Cloud Hosted (Future)

If a hosted version is built, the pricing would be:

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | 1 wiki, 100 pages, basic search |
| Pro | $10/mo | Unlimited wikis, unlimited pages, team sharing |
| Team | $29/mo/user | SSO, audit logs, priority support |
| Enterprise | Custom | Dedicated infra, SLA, custom integrations |

## Why Open Core?

The MCP server and all core tools are free. This ensures:

1. **No vendor lock-in**: Your data is markdown files you control
2. **Community contributions**: Anyone can improve the code
3. **Trust**: You can audit every line of code
4. **Longevity**: The project survives even if the company doesn't

Revenue from the cloud version funds continued open source development.

## Commercial Use

Commercial use is explicitly permitted under MIT. You can:
- Run WikiCapsule in your company
- Build products on top of it
- Offer WikiCapsule hosting to your customers
- Modify it for your needs

No attribution required (though appreciated).

## If Building SaaS

Stripe integration points:
- User signup → Stripe Customer creation
- Plan selection → Stripe Subscription
- Usage tracking → Metered billing for searches/ingests
- Team invites → Stripe Checkout for seat-based billing

These are documented as integration points but not implemented in the open source version.
