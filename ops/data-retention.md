# Data Retention

## Retention Philosophy

Git history IS the retention strategy. Every version of every page is preserved in git. The wiki is append-only by design — nothing is truly deleted, only superseded.

## Retention Policy

### Wiki Pages

- **Retention**: Permanent (in git)
- **Pruning**: Never delete wiki pages; mark as deprecated in frontmatter if needed
- **Migration**: Git history survives across servers

### Raw Sources

- **Retention**: Permanent by default (in git)
- **Large files**: Consider Git LFS for PDFs, images > 10MB
- **Archive**: After 2 years, compress old raw sources to `.tar.gz`

```bash
# Archive sources older than 2 years
cd raw && find . -type f -mtime +730 -exec tar -czf ../archive/$(date +%Y).tar.gz {} +
```

### Search Index

- **Retention**: Ephemeral (can be regenerated)
- **Regeneration**: `search.db` can be deleted and will rebuild on next startup
- **Backup**: Optional — speeds up recovery but not required

### Log Table

- **Retention**: 90 days in SQLite
- **Archival**: Older entries remain in `log.md` (git-tracked)
- **Pruning**: Run nightly:

```sql
DELETE FROM log WHERE timestamp < datetime('now', '-90 days');
```

### Lock Files

- **Retention**: Ephemeral
- **Cleanup**: Removed on graceful shutdown; stale locks auto-expire after 30s

## Backup Strategy

### Git-Based Backup

```bash
# Local bundle
git bundle create wiki-backup-$(date +%Y%m%d).bundle --all

# Remote mirror
git push backup-remote main

# Full directory (including search.db)
rsync -avz ~/wiki/ backup-server:~/wiki-backup/
```

### Recovery

```bash
# From git bundle
git clone wiki-backup-20240415.bundle ~/wiki-restored

# The search index will auto-rebuild on first run
python -m wikicapsule.server --wiki-dir ~/wiki-restored
```

## GDPR / Privacy

Since WikiCapsule runs locally:
- No third-party data processing
- No telemetry or analytics sent externally
- User controls all data
- Right to deletion: delete the wiki directory

For SaaS deployments (future), implement:
- Data export (markdown zip download)
- Account deletion (purge all user data)
- Retention limits (auto-delete after account closure)
