# Future — Extension Roadmap

The MCP server is the platform. Everything else is a differently-shaped client talking to the same git-backed markdown directory.

## Priority Stack

| Priority | Extension | Effort | Impact | Timeline |
|----------|-----------|--------|--------|----------|
| P0 | CLI (`wikicapsule` command) | Low | High | Shipped with core |
| P0 | VS Code via Cline/Roo | None | High | Document only |
| P1 | Obsidian Plugin | Low | Very High | Week 2 |
| P1 | Browser Extension | Medium | High | Week 3 |
| P2 | REST API wrapper | Medium | Medium | Week 4 |
| P2 | Web UI | Medium | Medium | Week 4 |
| P2 | Slack/Discord Bot | Medium | Medium | Week 5 |
| P3 | Mobile App | High | Low | SaaS only |
| P3 | Real-time Collaboration | Very High | Low | Probably never |

## CLI (Shipped)

Shell-native interface for power users:

```bash
wikicapsule init ./my-wiki
wikicapsule ingest ./article.md --tags="ml"
wikicapsule query "What did Karpathy say?"
wikicapsule lint --auto-fix
wikicapsule search "transformer" --limit=5
wikicapsule stats
wikicapsule log --tail=10
wikicapsule cat entities/karpathy.md
wikicapsule edit entities/karpathy.md
```

**Integrations**: `fzf` picker, git hooks, tmux status line, shell completions.

## VS Code Integration

No custom extension needed initially. Cline and Roo Code already speak MCP. Document the setup.

**Future custom extension**: Sidebar wiki graph, command palette integration, hover previews for wikilinks, status bar metrics.

## Obsidian Plugin (Week 2)

Highest-impact extension. Karpathy already uses Obsidian; this makes WikiCapsule native to that workflow.

**Features**:
- Sidebar "Ingest current note" button
- "Query WikiCapsule" modal with synthesized answers
- Graph view compatibility for wikilinks
- Auto-sync file watcher
- Status bar health indicator

**Tech**: TypeScript, Obsidian Plugin API.

## Browser Extension (Week 3)

One-click ingest from any web page. Manifest V3.

**Features**:
- Clip current page as markdown
- Highlight text → right-click → add as note
- Auto-download images to `raw/assets/`
- YouTube transcript extraction
- PDF text extraction

**Constraint**: MV3 background scripts have time limits. Long ingests need a relay server or 30s cap.

## REST API Wrapper (Week 4)

Thin REST layer over the MCP server for universal compatibility.

```
GET  /api/v1/wiki/pages
GET  /api/v1/wiki/pages/{path}
POST /api/v1/wiki/ingest
POST /api/v1/wiki/query
POST /api/v1/wiki/search
GET  /api/v1/wiki/stats
GET  /api/v1/wiki/log
GET  /api/v1/health
```

**Enables**: Mobile apps, Zapier/n8n, internal dashboards.

## Web UI (Week 4)

React-based frontend for non-technical users.

**Pages**:
- Browse: Rendered markdown with wikilink navigation
- Graph: Interactive force-directed graph (D3.js)
- Search: Full-text search with filters
- Ingest: Drag-drop upload, URL paste
- Query: Chat interface with streaming answers
- Admin: Lint reports, git history, config editor

## Team Integrations (Week 5)

**Slack Bot**: `/wikicapsule ingest [URL]`, `/wikicapsule query [question]`, auto-ingest `#knowledge` channel.

**Discord Bot**: Same pattern, different API.

**GitHub Actions**: `wikicapsule/ingest-action@v1` for PR ingest, scheduled lint.

## Migration Tools

**Notion → WikiCapsule**: Export as Markdown, parse blocks, preserve hierarchy. One-way only.

**Confluence → WikiCapsule**: Similar pipeline for enterprise teams. Preserve page hierarchy and attachments.

## Explicitly Out of Scope

- Two-way sync with Notion/Confluence (conflict resolution nightmare)
- Real-time collaboration + git (pick one model; we picked git)
- Native mobile app (unless SaaS revenue justifies it)
- Electron desktop app (Tauri if needed, but probably not)
- Embedding-based RAG infrastructure (we use local vectors; no Pinecone/Weaviate/ChromaDB)
- Multi-tenant SaaS (future commercial direction only)
