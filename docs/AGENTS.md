# AGENTS.md — Provider-Agnostic Agent Interaction Guide

How any AI agent (Claude, GPT-4, Gemini, local models) should interact with this codebase.

## Universal Principles

1. **This is an MCP server**. It speaks the Model Context Protocol. It does not call LLM APIs.
2. **The wiki is markdown + git**. All data lives in plain text files. No proprietary formats.
3. **The LLM reasons, the server manages**. The server handles files, search, and git. You handle synthesis and decisions.

## Getting Started

If you're reading this in an agent context, here's what to know:

### Project Structure

```
src/wikicapsule/
├── server.py          # MCP server entry — start here
├── tools.py           # Tool implementations — 7 tools
├── resources.py       # Resource handlers
├── prompts.py         # Workflow prompts
├── wiki.py            # Wiki operations engine
├── search.py          # Hybrid search (BM25 + vector)
├── git_manager.py     # Git with file locking
├── markdown.py        # Frontmatter + wikilink parser
├── config.py          # YAML configuration
├── models.py          # Pydantic models
└── cli.py             # Command-line interface
```

### Key Conventions

- **Paths**: All wiki paths are relative to `wiki/` directory (e.g., `entities/person.md`)
- **Frontmatter**: YAML block at top of every page with `title`, `type`, `tags`, `status`
- **Wikilinks**: Use `[[Page Name]]` for internal links
- **Kebab-case**: File names use hyphens: `my-page-name.md`
- **Git commits**: Every modification triggers an auto-commit with `[wikicapsule]` prefix

### MCP Tools Available

Your client (Claude Desktop, Cline, etc.) will expose these tools. Use them rather than direct file operations:

| Tool | When to Use |
|------|-------------|
| `wiki_ingest` | Adding a new source document |
| `wiki_query` | Finding relevant pages for a question |
| `wiki_search` | Full-text searching with BM25/vector/hybrid |
| `wiki_lint` | Checking wiki health |
| `wiki_create_page` | Writing a new wiki page |
| `wiki_update_page` | Updating an existing page |
| `wiki_get_stats` | Getting wiki metrics |

### MCP Resources Available

Read these to understand the wiki state:

| Resource | What It Contains |
|----------|-----------------|
| `wiki://index.md` | Catalog of all pages |
| `wiki://log.md` | Recent operations |
| `wiki://WIKI.md` | Schema and conventions |
| `wiki://wiki/{path}` | Any specific page |
| `wiki://raw/{path}` | Any raw source document |

## Working With This Codebase

### Adding a Feature

1. Read the relevant source files (start with `server.py`)
2. Check `tests/` for existing test patterns
3. Implement your changes
4. Add tests following the existing patterns
5. Run `pytest` to verify
6. Update this doc if you changed conventions

### Common Patterns

**Creating a tool that modifies the wiki:**
```python
from wikicapsule.git_manager import GitManager

with GitManager(wiki_dir=config.wiki_dir) as git:
    # Make your changes
    git.commit("operation_name", "description")
```

**Reading a wiki page:**
```python
page = wiki.get_page("entities/topic.md")
if page:
    title = page.frontmatter.title
    content = page.content
    links = page.wikilinks
```

**Searching:**
```python
results = wiki.search.search("query", limit=10, search_type="hybrid")
for r in results:
    print(f"{r.title}: {r.score:.3f}")
```

## Testing

```bash
pytest              # Run all tests
pytest -x         # Stop on first failure
pytest -k search  # Run tests matching 'search'
```

## Important Notes

- Don't hardcode paths. Use `config.wiki_path`, `config.raw_path`, etc.
- Don't skip the file lock when modifying the wiki. Use `GitManager`.
- Don't call LLM APIs from the server. That's the client's job.
- Keep the provider-agnostic spirit. No Claude-specific conventions in the core code.
