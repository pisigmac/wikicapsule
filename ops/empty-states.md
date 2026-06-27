# Empty States

What the wiki looks like before any ingests.

## Initial State

After `wikicapsule init`, the wiki contains:

```
my-wiki/
├── .wikicapsule/
│   ├── config.yaml    # Default configuration
│   ├── search.db      # Empty SQLite database
│   └── lock.json      # No lock
├── raw/               # Empty subdirectories
│   ├── articles/
│   ├── papers/
│   ├── books/
│   ├── transcripts/
│   └── assets/
├── wiki/
│   ├── index.md       # "No pages yet" message
│   ├── log.md         # "No activity yet" message
│   ├── overview.md    # Getting started guide
│   ├── entities/      # Empty
│   ├── concepts/      # Empty
│   ├── sources/       # Empty
│   ├── comparisons/   # Empty
│   └── explorations/  # Empty
└── WIKI.md            # Schema documentation
```

## index.md (Empty)

```markdown
# Wiki Index

> Auto-maintained catalog of all pages. Last updated: 2024-04-15 10:00 UTC

## Overview

This wiki is empty. Start by ingesting a source document.

## Pages by Category

### Entities (0)

_No pages yet._

### Concepts (0)

_No pages yet._

### Sources (0)

_No pages yet._

### Comparisons (0)

_No pages yet._

### Explorations (0)

_No pages yet._

## Recent Activity

No recent activity.
```

## log.md (Empty)

```markdown
# Wiki Log

> Chronological record of all operations. Append-only.

## Entries

---

*Log started: 2024-04-15*
```

## overview.md (Empty)

```markdown
# Wiki Overview

This wiki is empty. Start by ingesting a source document.

## Quick Start

1. Ingest your first source: Use the `wiki_ingest` tool with a file path or URL
2. Explore the wiki: Use `wiki_query` to ask questions
3. Keep it healthy: Run `wiki_lint` periodically
```

## First Ingest Experience

After the first ingest, the wiki populates:
- `raw/articles/` gets the source file
- `wiki/sources/` gets the source page
- `index.md` updates with the new source
- `log.md` gets the first entry

The user sees immediate value: their content is searchable and linked.

## Getting Started Guide in WIKI.md

The `WIKI.md` file contains a full schema reference that helps new users (both humans and AI agents) understand the wiki structure.
