# Events — Structured Logging

## Event Types

All operations emit structured log entries to the SQLite `log` table and the markdown `log.md`.

## Event Schema

```json
{
  "timestamp": "2024-04-15T10:30:00Z",
  "operation": "ingest",
  "summary": "Ingested article: Attention Is All You Need",
  "details": {
    "source_id": "abc123",
    "source_type": "paper",
    "duration_ms": 450,
    "pages_created": 1,
    "pages_updated": 0
  }
}
```

## Lifecycle Events

### ingest.start
- Emitted at the start of an ingest operation
- Contains: source_path, source_type, tags

### ingest.complete
- Emitted after successful ingest
- Contains: source_id, pages_created, duration_ms

### ingest.error
- Emitted on ingest failure
- Contains: error_message, source_path, stack_trace

### query.start
- Emitted at query start
- Contains: question, output_format

### query.complete
- Emitted after query results returned
- Contains: result_count, duration_ms, search_type

### search.start
- Emitted at search start
- Contains: query, search_type, limit

### search.complete
- Emitted after search results
- Contains: result_count, duration_ms, bm25_count, vector_count

### lint.start
- Emitted at lint start
- Contains: scope, auto_fix

### lint.complete
- Emitted after lint report
- Contains: issue_count, error_count, warning_count, info_count

### page.create
- Emitted on page creation
- Contains: path, title, type

### page.update
- Emitted on page update
- Contains: path, reason

## Structured Logging Format

Python logging configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
```

For production, switch to JSON:

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "operation": getattr(record, "operation", None),
        })
```

## Log Storage

- **SQLite `log` table**: Queryable, structured
- **Markdown `log.md`**: Human-readable, git-tracked
- **stderr**: Real-time, for container logging

## Log Rotation

SQLite log table grows over time. Prune old entries:

```sql
-- Keep 90 days of logs
DELETE FROM log WHERE timestamp < datetime('now', '-90 days');
```

Run via cron: `0 3 * * * sqlite3 /wiki/.wikicapsule/search.db "DELETE FROM log WHERE timestamp < datetime('now', '-90 days');"`
