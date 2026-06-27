# CLAUDE.md — Claude Code Interaction Guide

How Claude Code (and Claude Desktop) should interact with this codebase.

## Project Overview

WikiCapsule is an MCP server written in Python. It exposes a git-backed markdown wiki as MCP resources and tools. The server uses stdio transport by default.

## Key Files

| File | Purpose |
|------|---------|
| `src/wikicapsule/server.py` | MCP server entry point |
| `src/wikicapsule/tools.py` | 7 MCP tool implementations |
| `src/wikicapsule/resources.py` | Resource URI handlers |
| `src/wikicapsule/prompts.py` | Workflow prompt definitions |
| `src/wikicapsule/wiki.py` | Wiki directory operations |
| `src/wikicapsule/search.py` | Hybrid search engine |
| `src/wikicapsule/git_manager.py` | Git operations with locking |
| `src/wikicapsule/markdown.py` | Frontmatter and wikilink parsing |
| `src/wikicapsule/config.py` | Configuration management |
| `src/wikicapsule/models.py` | Pydantic data models |

## Common Tasks

### Running the Server

```bash
python -m wikicapsule.server --wiki-dir ./test-wiki --log-level DEBUG
```

### Running Tests

```bash
pytest                           # All tests
pytest tests/unit/               # Unit tests only
pytest tests/integration/        # Integration tests
pytest -v --tb=short            # Verbose with short tracebacks
```

### Adding a New Tool

1. Add the tool function in `src/wikicapsule/tools.py`
2. Register it inside `register_tools()` using the `@mcp.tool()` decorator
3. Add corresponding tests in `tests/unit/` or `tests/integration/`
4. Update `API.md` with the tool schema

### Adding a New Resource

1. Add the resource handler in `src/wikicapsule/resources.py`
2. Register it in `create_mcp_server()` in `server.py`
3. Update the resource discovery in `discover_wiki_pages()`

### Modifying the Search Engine

The search engine is in `src/wikicapsule/search.py`. Key methods:
- `index_page()` — add/update a page in the index
- `search_bm25()` — keyword search via FTS5
- `search_vector()` — semantic search via embeddings
- `search_hybrid()` — RRF fusion of both

When modifying search, run the integration tests:
```bash
pytest tests/integration/test_ingest_flow.py -v
```

## Code Style

- **Ruff** for linting and import sorting
- **MyPy** strict mode for type checking
- Line length: 100 characters
- Python 3.11+ features welcome (match statements, union types with `|`)

## Testing Philosophy

- Unit tests: Models, parsers, config — no I/O
- Integration tests: Full workflows with temp directories
- E2E tests: Server lifecycle with real MCP protocol
- All tests use `tmp_path` fixtures — no test pollution

## Git Workflow

- Main branch: `main`
- Feature branches: `feature/description`
- All changes go through PRs
- CI runs: pytest, mypy, ruff
