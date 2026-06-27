# Features

WikiCapsule feature list with implementation status.

## Core Features

| Feature | Status | Notes |
|---------|--------|-------|
| MCP stdio transport | Implemented | Default mode, production-ready |
| MCP SSE transport | Implemented | Configurable via `--transport sse` |
| Resource reading | Implemented | All `wiki://` URIs supported |
| Tool registration | Implemented | 7 tools with JSON schemas |
| Prompt registration | Implemented | 3 workflow prompts |
| Initialize handshake | Implemented | Full MCP protocol compliance |

## Wiki Management

| Feature | Status | Notes |
|---------|--------|-------|
| Directory structure creation | Implemented | Auto-creates on first run |
| Page CRUD | Implemented | Create, read, update (no delete — use git) |
| Ingest workflow | Implemented | 5 source types supported |
| Index auto-maintenance | Implemented | Rebuilt on every ingest/update |
| Log auto-maintenance | Implemented | Append-only operation log |
| Git integration | Implemented | Auto-commit on every modification |
| File locking | Implemented | JSON-based lock with 30s timeout |
| Atomic writes | Implemented | Temp file + rename pattern |
| Conflict detection | Implemented | Warns on dirty working tree |
| WIKI.md schema | Implemented | Provider-agnostic documentation |

## Search Engine

| Feature | Status | Notes |
|---------|--------|-------|
| BM25 keyword search | Implemented | SQLite FTS5 |
| Vector semantic search | Implemented | all-MiniLM-L6-v2, local |
| Hybrid RRF fusion | Implemented | Configurable alpha |
| Incremental indexing | Implemented | Rebuilt on ingest/update |
| Full-text snippets | Implemented | Context around matches |
| Configurable parameters | Implemented | Model, alpha, thresholds |

## Query & Lint

| Feature | Status | Notes |
|---------|--------|-------|
| Query dispatch | Implemented | Finds relevant pages |
| Orphan detection | Implemented | Pages with no wikilinks |
| Broken link detection | Implemented | Wikilinks to missing pages |
| Empty page detection | Implemented | Pages with <50 chars |
| Untagged page detection | Implemented | Missing tags warning |
| Draft rot detection | Implemented | Pages stuck in draft |
| Lint severity levels | Implemented | error/warning/info |
| Stats tool | Implemented | Comprehensive metrics |

## CLI

| Feature | Status | Notes |
|---------|--------|-------|
| `init` command | Implemented | Initialize wiki |
| `ingest` command | Implemented | Ingest sources |
| `query` command | Implemented | Query wiki |
| `search` command | Implemented | Search with options |
| `lint` command | Implemented | Run health checks |
| `stats` command | Implemented | Show metrics |
| `log` command | Implemented | Show recent entries |
| `cat` command | Implemented | Display page |
| `edit` command | Implemented | Open in $EDITOR |

## Planned Features

| Feature | Priority | Timeline |
|---------|----------|----------|
| Obsidian plugin | P1 | Week 2 |
| Browser extension | P1 | Week 3 |
| REST API wrapper | P2 | Week 4 |
| Web UI | P2 | Week 4 |
| Slack/Discord bot | P2 | Week 5 |
| VS Code extension | P3 | Future |
| Mobile app | P3 | SaaS only |
