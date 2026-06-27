# WikiCapsule

A production-grade MCP server implementing Karpathy's LLM Wiki pattern as a shareable, provider-agnostic knowledge capsule.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![MCP](https://img.shields.io/badge/MCP-1.0-purple.svg)

## What It Does

WikiCapsule turns a git-backed markdown directory into an MCP-compatible knowledge server. Any MCP client (Claude, Cline, Roo Code, etc.) can read, search, ingest, and maintain a persistent wiki that compounds across sessions.

**Key idea**: Your knowledge lives in markdown files under version control. The MCP server manages indexing, search, and git operations. The LLM handles reasoning and synthesis. You keep the data.

```
┌─────────────┐     stdio/SSE     ┌──────────────────┐
│ MCP Client  │ ◄────────────────►│ WikiCapsule MCP  │
│ (Claude)    │                   │ Server           │
└─────────────┘                   │ ┌── Resources    │
                                  │ ├── Tools        │
                                  │ └── Search       │
                                  └────────┬─────────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Git-backed  │
                                    │ Wiki Dir    │
                                    │ (markdown)  │
                                    └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Git
- uv (recommended) or pip

### Install

```bash
# Clone the repository
git clone https://github.com/pisigmac/wikicapsule.git
cd wikicapsule

# Install with uv
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Initialize a Wiki

```bash
# Create a new wiki directory
mkdir my-wiki && cd my-wiki

# Initialize the wiki structure
wikicapsule init

# Or use the MCP server directly
python -m wikicapsule.server --wiki-dir ./my-wiki
```

### Use with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "wikicapsule": {
      "command": "python",
      "args": ["-m", "wikicapsule.server", "--wiki-dir", "/path/to/my-wiki"]
    }
  }
}
```

Restart Claude Desktop. You'll see the wiki tools and resources available.

### First Ingest

```markdown
Ask Claude:

"Ingest this article about transformers into my wiki:
[ paste article content ]
"
```

Or use the CLI:

```bash
wikicapsule ingest ./article.md --type article --tags "ml,ai"
```

## Architecture

WikiCapsule follows a layered architecture:

| Layer | Components | Responsibility |
|-------|-----------|--------------|
| MCP Layer | `server.py`, `tools.py`, `resources.py`, `prompts.py` | Protocol handling |
| Wiki Layer | `wiki.py`, `markdown.py` | Directory operations, page CRUD |
| Search Layer | `search.py` | BM25 + vector hybrid search |
| Storage Layer | `git_manager.py`, SQLite | Persistence, version control |
| Config Layer | `config.py` | YAML-driven behavior |

## Tools (7)

| Tool | Purpose |
|------|---------|
| `wiki_ingest` | Add a source document to the wiki |
| `wiki_query` | Query the wiki and find relevant pages |
| `wiki_search` | Full-text search (BM25/vector/hybrid) |
| `wiki_lint` | Health-check the wiki |
| `wiki_create_page` | Create a new wiki page |
| `wiki_update_page` | Update an existing page |
| `wiki_get_stats` | Get wiki statistics |

## Resources

| Resource | Access |
|----------|--------|
| `wiki://index.md` | Catalog of all pages |
| `wiki://log.md` | Operation log |
| `wiki://WIKI.md` | Schema documentation |
| `wiki://wiki/{path}` | Any wiki page |
| `wiki://raw/{path}` | Any raw source |

## Prompts (3)

- **`ingest_workflow`** — Guided source ingestion
- **`query_workflow`** — Guided wiki querying
- **`lint_workflow`** — Guided health checking

## Search

WikiCapsule uses a hybrid search engine:

- **BM25** via SQLite FTS5 for keyword matching
- **Vector search** via sentence-transformers (all-MiniLM-L6-v2)
- **RRF fusion** to combine both signals

No API keys. No network calls. Everything stays local.

## Directory Structure

```
my-wiki/
├── .wikicapsule/
│   ├── search.db          # SQLite search index
│   ├── config.yaml        # Server configuration
│   └── lock.json          # Process lock
├── raw/                   # Immutable source documents
│   ├── articles/
│   ├── papers/
│   ├── books/
│   ├── transcripts/
│   └── assets/
├── wiki/                  # LLM-generated markdown
│   ├── index.md           # Auto-maintained catalog
│   ├── log.md             # Auto-maintained log
│   ├── overview.md        # High-level synthesis
│   ├── entities/          # People, orgs, products
│   ├── concepts/          # Ideas, theories
│   ├── sources/           # One page per source
│   ├── comparisons/       # Decision matrices
│   └── explorations/      # Query answers
├── WIKI.md                # Schema documentation
└── .git/                  # Version control
```

## Docker

```bash
docker-compose -f docker/docker-compose.yml up
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/wikicapsule

# Type checking
mypy src/wikicapsule

# Linting
ruff check src/wikicapsule
```

## Documentation

Full documentation is in the `docs/` directory:

- [FEATURES.md](docs/FEATURES.md) — Feature list and status
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Detailed architecture
- [API.md](docs/API.md) — MCP protocol documentation
- [TECH-STACK.md](docs/TECH-STACK.md) — Technology choices
- [DEPLOY.md](docs/DEPLOY.md) — Deployment guide
- [DB-SCHEMA.md](docs/DB-SCHEMA.md) — Database schema
- And 14 more...

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. See [CLAUDE.md](CLAUDE.md) and [AGENTS.md](AGENTS.md) for how to work with this codebase.

## Acknowledgments

- Andrej Karpathy for the LLM Wiki pattern
- Anthropic for the Model Context Protocol
- The sentence-transformers team for local embeddings
