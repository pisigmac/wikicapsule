# Feature Flags

All feature flags are config-driven via `config.yaml` or environment variables.

## Available Flags

| Flag | Config Path | Default | Description |
|------|-------------|---------|-------------|
| `enable_sse` | `server.transport` | `false` | Enable SSE transport mode |
| `enable_vector_search` | `wiki.search.vector_model` | `all-MiniLM-L6-v2` | Set to `null` to disable |
| `auto_commit` | `wiki.auto_commit` | `true` | Auto-commit on modifications |
| `stale_check_enabled` | `lint.stale_check_enabled` | `true` | Enable stale content detection |
| `extract_images` | `ingest.extract_images` | `true` | Download images during ingest |

## Usage

### Disable vector search (BM25 only)

```yaml
wiki:
  search:
    vector_model: null  # Disables vector search
```

Or set `hybrid_alpha: 0` for pure BM25:

```yaml
wiki:
  search:
    hybrid_alpha: 0.0  # 0 = pure BM25, 1 = pure vector
```

### Disable auto-commit

```yaml
wiki:
  auto_commit: false
```

With auto-commit disabled, changes accumulate in the working tree. Run `git commit` manually when ready.

### Disable stale checking

```yaml
lint:
  stale_check_enabled: false
```

## Runtime Overrides

Some flags can be set via environment variables for quick toggling:

```bash
# Quick disable vector search
WIKICAPSULE_SEARCH_VECTOR_MODEL=null python -m wikicapsule.server

# Disable auto-commit
WIKICAPSULE_WIKI_AUTO_COMMIT=false python -m wikicapsule.server
```

## Feature Flag Best Practices

1. **Default to enabled**: Features should work out of the box
2. **Document in ENV.md**: Every flag must be documented
3. **No runtime toggles**: Flags are read at startup, not changed mid-session
4. **Backward compatible**: Changing a flag default is a breaking change
