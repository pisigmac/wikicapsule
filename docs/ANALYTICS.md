# Analytics — Metrics to Track

## Product Metrics

| Metric | How to Track | Target |
|--------|-------------|--------|
| Ingest count | Log entries with operation=ingest | Growth rate > 10%/week |
| Query count | Log entries with operation=query | Daily active queries |
| Search count | Log entries with operation=search | < 500ms latency |
| Wiki growth | total_pages in stats | Consistent growth |
| Page diversity | Distribution across types | Healthy mix |

## Performance Metrics

| Metric | Measurement | Budget |
|--------|-------------|--------|
| Search latency | Time from query to results | p99 < 500ms |
| Query latency | Time from question to guidance | p99 < 2s |
| Ingest latency | Time per source | p99 < 5s |
| Index rebuild time | Full index regeneration | < 30s for 1000 pages |
| Server startup | Time to ready state | < 10s (including model load) |

## Quality Metrics

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Search relevance | Human rating of top-5 results | > 4/5 average |
| Lint issue count | wiki_lint results | Trending down |
| Orphan page ratio | orphans / total_pages | < 10% |
| Draft page ratio | drafts / total_pages | < 20% |
| Broken link count | wiki_lint --scope full | 0 |

## System Metrics

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Disk usage | search.db + wiki directory | > 80% |
| Memory usage | Python process | > 500MB |
| Git repo size | .git directory | > 1GB |
| Lock contention | lock.json staleness | > 3 incidents/day |

## Tracking Implementation

The SQLite `log` table captures all operations with timestamps. Query it for analytics:

```sql
-- Daily ingest count
SELECT date(timestamp), COUNT(*) FROM log WHERE operation = 'ingest' GROUP BY date(timestamp);

-- Average search latency (if logged)
SELECT AVG(details->>'latency_ms') FROM log WHERE operation = 'search';

-- Most active tags
SELECT json_extract(tags, '$[0]'), COUNT(*) FROM pages GROUP BY json_extract(tags, '$[0]');
```

For production deployments, export log entries to your analytics pipeline (Prometheus, Datadog, etc.).

## Dashboard (Future)

A built-in `/stats` endpoint (SSE mode) or `wiki_get_stats` output provides:
- Page counts by type and status
- Tag distribution
- Index size
- Recent activity

For the Web UI (future): full analytics dashboard with charts.
