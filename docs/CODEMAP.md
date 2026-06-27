# Code Map

Directory structure and module responsibilities.

```
wikicapsule/
├── src/wikicapsule/           # Main source code
│   ├── __init__.py            # Package init, version
│   ├── server.py              # MCP server entry point
│   ├── config.py              # Configuration loading & validation
│   ├── wiki.py                # Wiki directory operations engine
│   ├── git_manager.py         # Git wrapper with file locking
│   ├── search.py              # Hybrid search engine (BM25 + vector)
│   ├── markdown.py            # Frontmatter & wikilink parsing
│   ├── tools.py               # MCP tool implementations (7 tools)
│   ├── resources.py           # MCP resource handlers
│   ├── prompts.py             # MCP prompt definitions (3 prompts)
│   ├── models.py              # Pydantic data models
│   └── cli.py                 # Command-line interface
│
├── tests/
│   ├── unit/                  # Unit tests (no I/O)
│   │   ├── test_models.py     # Model validation tests
│   │   ├── test_config.py     # Configuration tests
│   │   ├── test_markdown.py   # Markdown parser tests
│   │   └── test_git_manager.py # Git operations tests
│   ├── integration/           # Integration tests
│   │   └── test_ingest_flow.py # Full workflow tests
│   └── e2e/                   # End-to-end tests
│       └── test_server_lifecycle.py # Server lifecycle tests
│
├── docker/
│   ├── Dockerfile             # Python 3.11 slim image
│   └── docker-compose.yml     # Stack definition
│
├── docs/                      # Documentation (20 files)
├── ops/                       # Operations configs (10 files)
├── config/
│   └── config.yaml            # Default configuration
├── sample-data/               # 5 test source documents
├── pyproject.toml             # Python project metadata
├── README.md                  # Project overview
└── WIKI.md                    # Provider-agnostic schema
```

## Module Details

### server.py

Entry point. Creates the `FastMCP` instance, registers resources, tools, and prompts. Handles both stdio and SSE transport modes.

**Key function**: `create_mcp_server(config)` → `FastMCP`

### config.py

Configuration management using Pydantic Settings. Supports YAML files, environment variables, and CLI overrides. Derives paths (wiki/, raw/, .wikicapsule/) from the wiki directory.

**Key class**: `WikiCapsuleConfig`

### wiki.py

Core wiki operations: page CRUD, ingest workflow, index/log maintenance, linting, statistics. Interacts with search engine and git manager.

**Key class**: `WikiManager`

### git_manager.py

Wraps `gitpython` with concurrency control:
- **Lock file**: `.wikicapsule/lock.json` with PID and timestamp
- **Timeout**: 30 seconds (configurable) before considering lock stale
- **Dirty detection**: Warns if working tree has uncommitted changes
- **Auto-commit**: Every modification triggers descriptive commit
- **Atomic operations**: Lock → check → modify → commit → release

### search.py

Hybrid search engine using SQLite FTS5 (BM25) and sentence-transformers (vector). RRF fusion for combining results. Incremental indexing.

**Key class**: `SearchEngine`

### markdown.py

Handles wiki page format:
- **Frontmatter**: YAML block with title, type, tags, sources, status
- **Wikilinks**: `[[Page Name]]` extraction and resolution
- **Content**: Body text, preview generation
- **Rendering**: Page → markdown string with frontmatter

**Key functions**: `parse_page()`, `extract_wikilinks()`, `create_page_content()`

### tools.py

MCP tool implementations. All 7 tools are registered here. Each tool handles validation, execution, and git commit.

**Key function**: `register_tools(mcp, wiki, config)`

### resources.py

MCP resource handlers. Reads wiki pages, raw documents, and auto-generated files (index, log, schema).

**Key function**: `read_resource(uri, wiki, config)` → `str`

### prompts.py

MCP prompt definitions for the 3 workflow prompts. Returns structured prompt messages for guided multi-step processes.

**Key function**: `get_prompt(name, arguments)` → `GetPromptResult`

### models.py

Pydantic models for all data structures: pages, requests, search results, lint issues, statistics. Centralizes validation logic.

### cli.py

Command-line interface using argparse. Commands: init, ingest, query, search, lint, stats, log, cat, edit.

**Key function**: `main()` → `int` (exit code)

## Data Flow

```
MCP Client → server.py → tools.py → wiki.py → git_manager.py
                                              → search.py
                                              → markdown.py
                         resources.py ← wiki.py ← filesystem
                         prompts.py (static)
```

## External Dependencies

| Dependency | Purpose |
|-----------|---------|
| `mcp` | MCP server SDK |
| `gitpython` | Git operations |
| `pyyaml` | YAML config parsing |
| `python-frontmatter` | Markdown frontmatter |
| `sentence-transformers` | Vector embeddings |
| `numpy` | Vector math |
| `pydantic` | Data validation |
| `markdown-it-py` | Markdown parsing |
