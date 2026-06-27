# Changelog

All notable changes to WikiCapsule.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] — 2024-04-15

### Added
- Initial release of WikiCapsule MCP Server
- stdio and SSE transport modes
- 7 MCP tools: wiki_ingest, wiki_query, wiki_search, wiki_lint, wiki_create_page, wiki_update_page, wiki_get_stats
- 5 MCP resources: wiki://index.md, wiki://log.md, wiki://WIKI.md, wiki://wiki/{path}, wiki://raw/{path}
- 3 MCP prompts: ingest_workflow, query_workflow, lint_workflow
- Hybrid search engine: BM25 (SQLite FTS5) + vector (sentence-transformers) + RRF fusion
- Git-backed wiki with auto-commits
- File locking for concurrent access
- YAML configuration system
- CLI with 9 commands: init, ingest, query, search, lint, stats, log, cat, edit
- 20 documentation deliverables
- 10 operations deliverables
- Docker and docker-compose support
- Comprehensive test suite (unit, integration, e2e)
- 5 sample source documents
- MIT license

### Architecture
- Layered architecture: MCP → Wiki → Search → Storage
- Pydantic models for all data structures
- Atomic file writes via temp file + rename
- Incremental search index updates
- Provider-agnostic WIKI.md schema

## [Unreleased]

### Planned
- Obsidian plugin
- Browser extension (Manifest V3)
- REST API wrapper
- Web UI (React)
- Slack/Discord bot
- GitHub Actions integration
- Performance benchmarks CI

### Under Consideration
- Cross-encoder reranking
- Larger embedding model support (all-mpnet-base-v2)
- Multi-wiki federation
- Notion/Confluence importers
- Collaborative editing via CRDTs

## Versioning

WikiCapsule follows [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes to MCP interface
- MINOR: New features, backwards compatible
- PATCH: Bug fixes, backwards compatible
