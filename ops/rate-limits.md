# Rate Limits

Per-tool rate limiting configuration.

## Default Limits

| Tool | Rate | Window |
|------|------|--------|
| wiki_ingest | 10/min | Sliding window |
| wiki_query | 60/min | Sliding window |
| wiki_search | 120/min | Sliding window |
| wiki_lint | 5/min | Sliding window |
| wiki_create_page | 30/min | Sliding window |
| wiki_update_page | 30/min | Sliding window |
| wiki_get_stats | 60/min | Sliding window |

## Implementation

Rate limiting is configurable in `config.yaml`:

```yaml
rate_limits:
  wiki_ingest: { requests: 10, window: 60 }
  wiki_query: { requests: 60, window: 60 }
  wiki_search: { requests: 120, window: 60 }
  wiki_lint: { requests: 5, window: 60 }
```

## Response

When rate limited, the tool returns:

```markdown
Rate limit exceeded for wiki_search. Limit: 120/min.
Retry after: 45 seconds.
```

## Implementation Notes

- Uses in-memory sliding window counter
- Per-process (not distributed)
- For multi-instance deployments, use Redis as shared counter
- Rate limits are logged at INFO level
