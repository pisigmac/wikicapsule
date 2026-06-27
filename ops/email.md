# Email

N/A for the open source project.

WikiCapsule is a local MCP server and doesn't send emails.

## If Building SaaS

Add welcome emails and notifications:

### Welcome Email
- Triggered on wiki creation
- Contains getting started guide
- Links to documentation

### Digest Email (Optional)
- Weekly summary of wiki activity
- New pages, updates, lint issues
- Customizable frequency

### Implementation

Use a transactional email service:
- **Resend** — developer-friendly, good deliverability
- **SendGrid** — established, good templates
- **AWS SES** — cost-effective at scale

### Template

```
Subject: Your WikiCapsule wiki is ready

Hi {{name}},

Your wiki "{{wiki_name}}" is ready to use.

Get started:
1. Add the MCP server to your AI client
2. Ingest your first source: wiki_ingest("./article.md", "article")
3. Query your knowledge: wiki_query("What do I know about...?")

Docs: https://docs.wikicapsule.io
Support: https://github.com/pisigmac/wikicapsule/issues

Happy knowledge building!
```
