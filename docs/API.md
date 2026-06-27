# API Documentation — MCP Protocol Interface

Full documentation of WikiCapsule's MCP protocol interface.

## Overview

WikiCapsule implements the Model Context Protocol (MCP) specification. It exposes resources (read-only data), tools (functions the LLM can call), and prompts (workflow templates).

## Transport

- **Primary**: stdio (default)
- **Optional**: SSE (configure via `--transport sse` or env var)

## Server Capabilities

On initialization, the server announces:

```json
{
  "resources": {
    "subscribe": false,
    "listChanged": false
  },
  "tools": {
    "listChanged": false
  },
  "prompts": {
    "listChanged": false
  }
}
```

## Resources

Resources are read-only data accessed via URI. All WikiCapsule resources use the `wiki://` scheme.

### Core Resources

#### `wiki://index.md`

Auto-maintained catalog of all wiki pages. Rebuilt on every ingest or page update.

**MIME type**: `text/markdown`

**Content**: Structured markdown with pages grouped by category (entities, concepts, sources, comparisons, explorations).

#### `wiki://log.md`

Chronological append-only log of all operations.

**MIME type**: `text/markdown`

**Content**: Timestamped entries for every ingest, query, lint, create, and update operation.

#### `wiki://WIKI.md`

Provider-agnostic schema documentation that explains the wiki structure to any AI agent.

**MIME type**: `text/markdown`

#### `wiki://wiki/{path}`

Any individual wiki page. The path is relative to the `wiki/` directory.

**Examples**:
- `wiki://wiki/entities/karpathy.md`
- `wiki://wiki/concepts/transformer-architecture.md`
- `wiki://wiki/sources/abc123.md`

**MIME type**: `text/markdown`

**404 behavior**: Returns error if page doesn't exist.

#### `wiki://raw/{path}`

Any raw source document. The path is relative to the `raw/` directory.

**Examples**:
- `wiki://raw/articles/sample-article.md`
- `wiki://raw/papers/attention-is-all-you-need.md`

**MIME type**: `text/markdown` for `.md` files, `application/octet-stream` for others.

## Tools

### `wiki_ingest`

Ingest a source document into the wiki.

**Input schema**:
```json
{
  "source_path": "string — Path to source file or URL",
  "source_type": "string — One of: article, paper, book_chapter, transcript, note",
  "tags": "string[] — Optional topic tags"
}
```

**Returns**: Markdown summary with source ID, paths, and title.

**Side effects**:
- Creates raw file in `raw/{type}/`
- Creates wiki page in `sources/`
- Updates `index.md`
- Appends to `log.md`
- Triggers git commit
- Updates search index

---

### `wiki_query`

Query the wiki and get relevant pages.

**Input schema**:
```json
{
  "question": "string — Natural language question",
  "output_format": "string — markdown/table/slides/chart (default: markdown)"
}
```

**Returns**: Search results with guidance for synthesizing an answer.

**Note**: This tool finds relevant pages. The LLM client synthesizes the actual answer by reading those pages.

---

### `wiki_search`

Full-text search over wiki pages.

**Input schema**:
```json
{
  "query": "string — Search query",
  "limit": "integer — Max results, 1-100 (default: 10)",
  "type": "string — bm25/vector/hybrid (default: hybrid)"
}
```

**Returns**: Ranked results with scores and snippets.

---

### `wiki_lint`

Health-check the wiki.

**Input schema**:
```json
{
  "scope": "string — quick or full (default: quick)",
  "auto_fix": "boolean — Auto-fix where possible (default: false)"
}
```

**Returns**: Report with issues categorized as error/warning/info.

**Checks performed**:
- Orphan pages (no incoming wikilinks)
- Broken wikilinks
- Empty pages
- Untagged pages
- Draft rot

---

### `wiki_create_page`

Create a new wiki page.

**Input schema**:
```json
{
  "path": "string — Wiki path, e.g., entities/new-topic.md",
  "content": "string — Markdown content",
  "tags": "string[] — Optional tags"
}
```

**Returns**: Confirmation with created path.

**Side effects**: Creates file, updates index, git commit, search index update.

---

### `wiki_update_page`

Update an existing wiki page.

**Input schema**:
```json
{
  "path": "string — Wiki path",
  "content": "string — New markdown content (replaces existing)",
  "reason": "string — Why this update is being made"
}
```

**Returns**: Confirmation with update reason.

---

### `wiki_get_stats`

Get wiki statistics.

**Input**: None (no parameters)

**Returns**: Formatted statistics including page counts, tag distribution, index size.

## Prompts

### `ingest_workflow`

Guides the LLM through the 7-step ingest process.

**Arguments**:
- `source_path` (required): Path or URL to source
- `source_type` (required): Type of source

**Steps covered**:
1. Read and understand the source
2. Discuss key insights
3. Create source page
4. Update entity pages
5. Update concept pages
6. Verify index
7. Confirm log entry

---

### `query_workflow`

Guides the LLM through querying the wiki.

**Arguments**:
- `question` (required): The question to answer

**Steps covered**:
1. Read the wiki index
2. Search for relevant pages
3. Read top pages
4. Synthesize an answer with citations
5. Optionally file as exploration

---

### `lint_workflow`

Guides the LLM through linting the wiki.

**Arguments**:
- `scope` (optional): `quick` or `full`

**Steps covered**:
1. Run lint check
2. Review contradictions
3. Check stale content
4. Fix orphans
5. Address missing pages
6. Verify index integrity

## Error Handling

All tools return error messages as markdown strings rather than throwing protocol-level errors. This ensures the LLM can see what went wrong and potentially retry or work around the issue.

Common error patterns:
- **File exists**: Suggests using `wiki_update_page` instead of `wiki_create_page`
- **File not found**: Suggests creating the page first
- **Invalid input**: Describes the validation failure
- **Git conflicts**: Suggests running `wiki_lint` or manual resolution

## Protocol Notes

- All resource reads are synchronous
- All tool invocations are synchronous
- The server maintains no session state
- The wiki directory is the single source of truth
- Concurrent access is managed via file locking, not transactions
