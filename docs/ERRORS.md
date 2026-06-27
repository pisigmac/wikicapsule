# Errors — Error Code Reference & Troubleshooting

## Error Categories

WikiCapsule returns descriptive error messages rather than numeric codes. This doc catalogs common errors and their resolutions.

## Configuration Errors

### Invalid transport mode

**Message**: `transport must be 'stdio' or 'sse'`

**Cause**: `WIKICAPSULE_TRANSPORT` or config has invalid value.

**Fix**: Set to `stdio` (default) or `sse`.

### Missing wiki directory

**Message**: Wiki directory not found or not accessible.

**Cause**: The wiki directory doesn't exist.

**Fix**: Create it (`mkdir -p ~/wiki`) or run `wikicapsule init`.

## Tool Errors

### Invalid source_type

**Message**: `source_type must be one of {allowed}`

**Cause**: Passed an invalid source type to `wiki_ingest`.

**Fix**: Use one of: `article`, `paper`, `book_chapter`, `transcript`, `note`.

### Page already exists

**Message**: `Page already exists: {path}. Use wiki_update_page to modify it.`

**Cause**: `wiki_create_page` called with an existing path.

**Fix**: Use `wiki_update_page` instead, or choose a different path.

### Page not found

**Message**: `Page not found: {path}`

**Cause**: `wiki_update_page` called with a non-existent path.

**Fix**: Use `wiki_create_page` first, or check the path spelling.

### Lock timeout

**Message**: `Could not acquire lock within {timeout}s`

**Cause**: Another process holds the file lock and hasn't released it.

**Fix**:
1. Check if another WikiCapsule instance is running
2. If the lock is stale (process crashed), it will auto-release after the timeout
3. Manually delete `.wikicapsule/lock.json` if you're sure no process is active

## Git Errors

### Dirty working tree

**Message**: `Working tree has uncommitted changes. Commit or stash them before proceeding.`

**Cause**: Git working tree has uncommitted changes when a tool tried to acquire the lock.

**Fix**:
1. Commit the changes: `cd ~/wiki && git add . && git commit -m "manual commit"`
2. Or stash them: `git stash`
3. Or run `wiki_lint` which may auto-fix some issues

### Git commit failed

**Message**: `Git commit failed: {details}`

**Cause**: Git operation error (disk full, permission denied, etc.).

**Fix**: Check disk space, permissions, and git configuration.

## Search Errors

### Model not found

**Message**: Model download or loading failure.

**Cause**: sentence-transformers can't download or load the model.

**Fix**:
1. Check internet connection (first download only)
2. Verify disk space (~80MB for all-MiniLM-L6-v2)
3. Set `SENTENCE_TRANSFORMERS_HOME` to a writable directory
4. Pre-download: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`

### Empty search results

**Message**: `No results found for '{query}'`

**Cause**: No indexed pages match the query.

**Fix**: Ingest some sources first, or try a different query.

## Performance Issues

### Slow search

**Symptom**: Searches take > 500ms.

**Possible causes**:
- Very large wiki (10K+ pages)
- Slow disk (network drive)
- Embedding model on CPU without acceleration

**Fixes**:
- Enable SQLite WAL mode
- Use SSD for wiki directory
- Reduce hybrid_alpha to favor BM25
- Consider a larger embedding model if quality is the bottleneck

### High memory usage

**Symptom**: Python process using > 500MB.

**Possible causes**:
- sentence-transformers model loaded
- Large SQLite result sets

**Fixes**:
- This is expected (~150MB for the model)
- For constrained environments, use a smaller model

## Logging

Enable debug logging for detailed diagnostics:

```bash
python -m wikicapsule.server --log-level DEBUG
```

Debug logs include:
- Lock acquire/release with PID and timestamp
- Search timing (BM25, vector, fusion)
- Git operations with commit hashes
- Index rebuild timing

## Getting Help

1. Check this document for your error
2. Enable debug logging and check logs
3. Run `wiki_lint --scope full` to check wiki health
4. Open an issue on GitHub with the error message and debug logs
