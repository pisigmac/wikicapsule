# Environment Variables & Configuration

WikiCapsule can be configured via environment variables, YAML config file, or CLI arguments. Priority: CLI args > env vars > config file > defaults.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WIKICAPSULE_WIKI_DIR` | `.` | Root wiki directory |
| `WIKICAPSULE_TRANSPORT` | `stdio` | Transport: `stdio` or `sse` |
| `WIKICAPSULE_PORT` | `8080` | Port for SSE mode |
| `WIKICAPSULE_LOG_LEVEL` | `INFO` | Logging: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Config File

Location: `{wiki_dir}/.wikicapsule/config.yaml`

```yaml
server:
  transport: stdio        # stdio or sse
  port: 8080            # SSE port
  log_level: INFO

wiki:
  auto_commit: true
  commit_message_template: "[wikicapsule] {operation}: {summary}"
  lock_timeout_seconds: 30
  search:
    vector_model: "all-MiniLM-L6-v2"
    hybrid_alpha: 0.5     # 0=BM25 only, 1=vector only
    rebuild_threshold: 10  # Rebuild index after N changes

ingest:
  default_tags: []
  extract_images: true
  summary_max_length: 2000

lint:
  orphan_threshold_days: 30
  stale_check_enabled: true
```

## CLI Arguments

```bash
python -m wikicapsule.server \
  --wiki-dir ./my-wiki \
  --transport stdio \
  --port 8080 \
  --log-level INFO \
  --config /path/to/config.yaml
```

## Configuration Priority

1. CLI arguments (highest)
2. Environment variables
3. Config file (`{wiki_dir}/.wikicapsule/config.yaml`)
4. Built-in defaults (lowest)

## Examples

### Claude Desktop (macOS)

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wikicapsule": {
      "command": "python",
      "args": [
        "-m", "wikicapsule.server",
        "--wiki-dir", "/Users/you/wiki",
        "--log-level", "INFO"
      ],
      "env": {
        "WIKICAPSULE_WIKI_DIR": "/Users/you/wiki"
      }
    }
  }
}
```

### Docker

```yaml
environment:
  - WIKICAPSULE_WIKI_DIR=/wiki
  - WIKICAPSULE_TRANSPORT=stdio
  - WIKICAPSULE_LOG_LEVEL=INFO
```

### Multiple Wikis

Use different directories with separate configs:

```bash
# Work wiki
python -m wikicapsule.server --wiki-dir ~/wiki/work --port 8081

# Personal wiki
python -m wikicapsule.server --wiki-dir ~/wiki/personal --port 8082
```

## Sensitive Configuration

No API keys or secrets are required. WikiCapsule is designed to run entirely offline.

If you add integrations (future), store secrets in:
- Environment variables (recommended)
- `.env` file (gitignored)
- Your system's keychain

Never commit secrets to the wiki git repository.
