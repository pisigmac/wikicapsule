# OpenAPI-Style Spec

Although MCP is not an HTTP protocol, this document structurally maps WikiCapsule's interface in an OpenAPI-inspired format for clarity.

## Servers

- **stdio**: `stdio://wikicapsule` (default)
- **SSE**: `http://localhost:8080` (optional)

## Resources

### GET wiki://index.md

Returns the auto-maintained wiki index.

**Response**: `text/markdown`

### GET wiki://log.md

Returns the operation log.

**Response**: `text/markdown`

### GET wiki://WIKI.md

Returns the schema documentation.

**Response**: `text/markdown`

### GET wiki://wiki/{path}

Returns a specific wiki page.

**Parameters**:
- `path` (path): Relative path in wiki/ directory

**Response**: `text/markdown`

**Errors**:
- 404: Page not found

### GET wiki://raw/{path}

Returns a raw source document.

**Parameters**:
- `path` (path): Relative path in raw/ directory

**Response**: `text/markdown` or `application/octet-stream`

**Errors**:
- 404: Document not found

## Tools

### wiki_ingest

**Input schema** (JSON):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "source_path": {"type": "string", "description": "Path to source file or URL"},
    "source_type": {
      "type": "string",
      "enum": ["article", "paper", "book_chapter", "transcript", "note"]
    },
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["source_path", "source_type"]
}
```

**Response**: Markdown string with operation summary.

### wiki_query

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "question": {"type": "string", "minLength": 1},
    "output_format": {"type": "string", "enum": ["markdown", "table", "slides", "chart"], "default": "markdown"}
  },
  "required": ["question"]
}
```

**Response**: Markdown string with search results and guidance.

### wiki_search

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string", "minLength": 1},
    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
    "type": {"type": "string", "enum": ["bm25", "vector", "hybrid"], "default": "hybrid"}
  },
  "required": ["query"]
}
```

**Response**: Markdown string with ranked results.

### wiki_lint

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "scope": {"type": "string", "enum": ["quick", "full"], "default": "quick"},
    "auto_fix": {"type": "boolean", "default": false}
  }
}
```

**Response**: Markdown string with lint report.

### wiki_create_page

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_\\-\\/]*\\.md$"},
    "content": {"type": "string", "minLength": 1},
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["path", "content"]
}
```

**Response**: Markdown string with confirmation.

### wiki_update_page

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {"type": "string"},
    "content": {"type": "string", "minLength": 1},
    "reason": {"type": "string", "minLength": 1}
  },
  "required": ["path", "content", "reason"]
}
```

**Response**: Markdown string with confirmation.

### wiki_get_stats

**Input**: None (no parameters)

**Response**: Markdown string with statistics.

## Prompts

### ingest_workflow

**Arguments**:
- `source_path` (string, required)
- `source_type` (string, required)

### query_workflow

**Arguments**:
- `question` (string, required)

### lint_workflow

**Arguments**:
- `scope` (string, optional, default: "quick")
