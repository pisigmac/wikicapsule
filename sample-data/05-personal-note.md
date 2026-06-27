# Research Notes — April 2024

**Author**: Personal research notebook
**Date**: 2024-04-10
**Tags**: llm, agents, mcp, knowledge-management

---

## Ideas

### Wiki as Knowledge Capsule

Been thinking about Karpathy's LLM Wiki pattern. The core idea: maintain a markdown-based knowledge base that compounds over time. Each conversation with an LLM can read from and write to the wiki, making knowledge persist across sessions.

Key principles:
1. **Markdown-native**: Human readable, version controllable
2. **Git-backed**: Full history, branching, collaboration
3. **Provider-agnostic**: Works with Claude, GPT-4, Gemini, local models
4. **Structured but flexible**: Frontmatter for metadata, freeform content

### MCP Server for Wikis

What if the wiki itself was an MCP server? Instead of the LLM managing files directly, it uses MCP tools:

- `wiki_ingest` — add a new source
- `wiki_query` — search and retrieve relevant pages
- `wiki_search` — full-text search
- `wiki_lint` — health check

This gives us:
- Clean separation of concerns
- Protocol-level schema validation
- Multiple client support (Claude, Cline, custom scripts)
- Composable with other MCP servers

### Hybrid Search

For the search backend, I'm thinking:
- **BM25** via SQLite FTS5 for keyword matching
- **Vector search** via sentence-transformers for semantic similarity
- **RRF fusion** to combine both signals

This keeps everything local — no API keys, no network calls, no latency spikes. The tradeoff is embedding quality, but all-MiniLM-L6-v2 is surprisingly good for general knowledge tasks.

## Implementation Notes

### File Locking

Need a simple file lock for concurrent access. JSON-based lock file with PID and timestamp. Timeout after 30 seconds to handle crashed processes.

### Atomic Writes

Write to temp file, then atomic rename. Prevents corruption if the process crashes mid-write.

### Git Integration

Every tool invocation that modifies state should trigger a git commit. This gives us:
- Full audit trail
- Ability to roll back changes
- Collaboration via git remotes

### Config-Driven

All behavior should be configurable via YAML:
- Transport mode (stdio vs SSE)
- Search parameters (model, hybrid alpha)
- Ingest settings (max summary length, default tags)
- Lint thresholds (orphan timeout, stale check)

## Questions to Explore

1. How well does hybrid search work with 1000+ pages? Need to benchmark.
2. What's the startup time with sentence-transformers? First load downloads the model.
3. Can we support multiple wikis? Like git worktrees but for knowledge bases.
4. Should there be a web UI for non-technical users? Probably, but out of scope for MVP.

## References

- Karpathy's LLM Wiki blog post
- MCP specification (modelcontextprotocol.io)
- SQLite FTS5 documentation
- sentence-transformers docs

## Next Steps

1. Build the core MCP server with stdio transport
2. Implement all 7 tools
3. Add the 3 workflow prompts
4. Write comprehensive tests
5. Dockerize for easy deployment
6. Document everything

Goal: Have a working prototype by end of April. Ship v0.1.0 by mid-May.
