# Performance Budget

Defined latency targets for all operations.

## Targets

| Operation | p50 | p99 | Measurement |
|-----------|-----|-----|-------------|
| Search (hybrid) | 50ms | 500ms | Query to results |
| Query | 200ms | 2000ms | Question to guidance |
| Ingest | 500ms | 5000ms | Per source document |
| Page create | 100ms | 500ms | Request to confirmation |
| Page update | 100ms | 500ms | Request to confirmation |
| Lint (quick) | 200ms | 1000ms | Full wiki scan |
| Lint (full) | 1000ms | 5000ms | Full wiki scan |
| Stats | 50ms | 200ms | Request to response |
| Server startup | 3000ms | 10000ms | Including model load |

## Methodology

Measured on reference hardware:
- CPU: 4 cores (Apple M1 or equivalent)
- RAM: 8GB
- Disk: SSD
- Wiki size: 100 pages, 50 sources

## Monitoring

Performance is tracked via:
1. **E2E tests**: `test_search_latency`, `test_query_latency`
2. **Log entries**: Each operation logs elapsed time
3. **CI benchmarks**: Performance regression detection

## Optimization Strategies

If targets are exceeded:

### Search
- Enable SQLite WAL mode
- Reduce vector model size
- Increase hybrid_alpha to favor BM25
- Add result caching for common queries

### Ingest
- Batch index updates (current: per-ingest)
- Async embedding computation
- Skip image extraction for text-only sources

### Startup
- Lazy-load embedding model (on first search)
- Preload in background thread
- Use smaller model for faster startup

## Load Testing

```bash
# Simulate 100 concurrent searches
locust -f tests/load/search.py --host mcp://wikicapsule

# Simulate sustained ingest load
locust -f tests/load/ingest.py --host mcp://wikicapsule
```

(Currently manual; planned for CI integration.)
