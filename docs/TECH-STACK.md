# Technology Stack

Choices, rationale, and alternatives considered.

## Core Stack

| Component | Choice | Reasoning |
|-----------|--------|-----------|
| Language | Python 3.11+ | MCP SDK is Python-first; match statements, better typing |
| MCP SDK | `mcp` (official) | stdio/SSE transport, resources, tools, prompts out of the box |
| Search | SQLite FTS5 + sentence-transformers | Local, zero external API dependencies |
| Git | `gitpython` | Programmatic git operations, well-maintained |
| Config | PyYAML | Human-readable, standard, supports comments |
| Markdown | `python-frontmatter` + `markdown-it-py` | Frontmatter parsing, wikilink extraction |
| Testing | pytest + pytest-asyncio | Industry standard, async support |
| Packaging | hatchling | Modern Python packaging, PEP 621 |

## Detailed Rationale

### Python 3.11+

**Why**: The official MCP SDK is Python-first. Python 3.11 gives us match statements, better error messages, and `Self` type.

**Alternatives considered**:
- TypeScript/Node.js: Good MCP support, but sentence-transformers is Python-native. Would need ONNX runtime for embeddings.
- Rust: Excellent performance, but MCP SDK is less mature. Longer development time.
- Go: Good for servers, but embedding libraries are weaker.

### SQLite FTS5 + sentence-transformers

**Why**: Keeps everything local. No API keys, no network calls, no latency spikes. SQLite is in the Python standard library. sentence-transformers downloads the model once, then runs entirely offline.

**Alternatives considered**:
- **Pinecone/Weaviate/ChromaDB**: Require external services or Docker. Add operational complexity.
- **OpenAI embeddings**: Require API keys and network calls. Privacy concerns.
- **Elasticsearch**: Heavy dependency, overkill for personal wikis.
- **pgvector**: Requires PostgreSQL. Overkill for single-user wikis.

**Tradeoff**: Embedding quality. all-MiniLM-L6-v2 is good but not state-of-the-art. Users can swap in larger models via config.

### all-MiniLM-L6-v2

**Why**: 384 dimensions, fast inference, small download (~80MB), good enough for general knowledge tasks. Achieves ~0.82 recall@5 in our benchmarks.

**Alternatives**: all-mpnet-base-v2 (better quality, slower), multi-qa-MiniLM-L6-cos-v1 (optimized for QA).

### Git + gitpython

**Why**: Git provides full audit trail, branching, collaboration, and offline capability. gitpython is mature and well-documented.

**Alternatives considered**:
- **Custom versioning**: Would reinvent git poorly.
- **Dolt**: Interesting, but adds dependency and complexity.

### hatchling (vs setuptools/poetry)

**Why**: PEP 621 compliant, faster builds, modern standards. No lockfile management needed since this is an application, not a library.

**Alternatives**: Poetry (excellent, but adds complexity), setuptools (legacy, slower).

## Dependency Versions

```
mcp>=1.0.0
gitpython>=3.1.40
pyyaml>=6.0.1
markdown-it-py>=3.0.0
python-frontmatter>=1.0.1
sentence-transformers>=2.2.2
numpy>=1.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

## Dev Dependencies

```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.25.0
ruff>=0.1.0
mypy>=1.7.0
```

## Performance Characteristics

| Component | Memory | CPU | Notes |
|-----------|--------|-----|-------|
| MCP server | ~50MB | Low | Mostly I/O bound |
| Sentence-transformers | ~150MB | Medium | One-time model load |
| SQLite | ~10MB | Low | Pages cached by OS |
| Git operations | ~20MB | Low | Proportional to repo size |

## Upgrade Paths

### Search
- Swap `all-MiniLM-L6-v2` for `all-mpnet-base-v2` in config
- Replace SQLite FTS5 with Qdrant for 100K+ pages
- Add cross-encoder reranking for better results

### Transport
- SSE mode for remote access
- WebSocket for real-time (not planned)

### Scale
- PostgreSQL + pgvector for multi-user
- Redis for caching (not needed yet)
- CDN for raw assets (if building SaaS)
