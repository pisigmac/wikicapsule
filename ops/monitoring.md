# Monitoring

## Health Check

### SSE Mode

```
GET /health

Response:
{
  "status": "healthy",
  "wiki_dir": "/wiki",
  "indexed_pages": 42,
  "db_size_mb": 12.5,
  "git_commits": 156,
  "uptime_seconds": 3600
}
```

### stdio Mode

Health is implicit — if the process is running, it's healthy. Check via process manager:

```bash
pgrep -f "wikicapsule.server" > /dev/null && echo "healthy" || echo "down"
```

## Prometheus Metrics (Future)

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

search_requests = Counter('wikicapsule_search_total', 'Search requests', ['search_type'])
search_duration = Histogram('wikicapsule_search_duration_seconds', 'Search latency')
ingest_requests = Counter('wikicapsule_ingest_total', 'Ingest requests', ['source_type'])
wiki_pages = Gauge('wikicapsule_wiki_pages_total', 'Total wiki pages', ['page_type'])
wiki_sources = Gauge('wikicapsule_wiki_sources_total', 'Total ingested sources')
```

## Grafana Dashboard

### Panels
- **Requests/sec**: By tool type
- **Latency p99**: By operation
- **Wiki growth**: Pages over time
- **Error rate**: Failed operations
- **Disk usage**: search.db size
- **Git activity**: Commits per day

## Log Monitoring

Structured logs can be shipped to:
- **Datadog**: JSON logs with service tags
- **Splunk**: Field extraction from JSON
- **CloudWatch**: AWS-native, alarms
- **Grafana Loki**: Lightweight, integrates with Grafana

## Alerts

| Condition | Severity | Action |
|-----------|----------|--------|
| Search p99 > 500ms | Warning | Check index size |
| Ingest error rate > 5% | Critical | Check disk space |
| Disk usage > 80% | Warning | Clean up or expand |
| Lock timeout > 3/hour | Critical | Investigate deadlocks |
| Git repo > 1GB | Warning | Run git gc |

## Local Monitoring

For self-hosted instances, use simple scripts:

```bash
#!/bin/bash
# check-health.sh
WIKI_DIR=${1:-~/wiki}

if [ ! -f "$WIKI_DIR/.wikicapsule/search.db" ]; then
    echo "CRITICAL: Search database missing"
    exit 2
fi

DB_SIZE=$(du -m "$WIKI_DIR/.wikicapsule/search.db" | cut -f1)
if [ "$DB_SIZE" -gt 500 ]; then
    echo "WARNING: Database size ${DB_SIZE}MB"
    exit 1
fi

echo "OK: Wiki healthy (${DB_SIZE}MB)"
exit 0
```
