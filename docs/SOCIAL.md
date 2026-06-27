# Social — Launch Copy

## Twitter/X Launch Thread

**Tweet 1 (Hook)**
Tired of losing knowledge across AI chat sessions?

I built WikiCapsule — an MCP server that turns markdown files into a compounding knowledge base.

Your AI can read it, write to it, and keep it organized. Automatically.

Thread

**Tweet 2 (Problem)**
Every time I chat with Claude, we build great knowledge together.

Then the session ends. And it's gone.

Notes apps don't help — they're not designed for AI workflows.

**Tweet 3 (Solution)**
WikiCapsule is different:
- MCP-native (works with Claude, GPT-4, Gemini...)
- Git-backed (full version history)
- Local-first (no cloud needed)
- Markdown (you own your data)

**Tweet 4 (How it works)**
1. Chat with your AI about a topic
2. It files insights in your wiki automatically
3. Next session, it reads what you built
4. Knowledge compounds over time

**Tweet 5 (Search)**
Built-in hybrid search:
- BM25 for keyword matching (via SQLite FTS5)
- Vector search for semantic similarity (local embeddings)
- RRF fusion combining both

No API keys. No cloud calls. Everything stays local.

**Tweet 6 (Code)**
It's open source (MIT):

git clone https://github.com/pisigmac/wikicapsule.git
pip install -e ".[dev]"

Then add to Claude Desktop config and go.

**Tweet 7 (CTA)**
Try it out. Star the repo. Open an issue.

If you've been looking for a way to make your AI conversations actually compound, this might be it.

https://github.com/pisigmac/wikicapsule

---

## Hacker News Post

**Title**: Show HN: WikiCapsule — Git-backed knowledge base as an MCP server

**Body**:

Hi HN,

I've been frustrated that knowledge built during AI chat sessions disappears when the session ends. So I built WikiCapsule — an MCP server that manages a git-backed markdown wiki.

The core idea: your AI assistant reads from and writes to a shared knowledge base that persists across sessions. Over time, it compounds.

Key features:
- MCP-native (works with Claude, GPT-4, any MCP client)
- Git-backed (full history, branching, collaboration)
- Local hybrid search (BM25 + sentence-transformers, no API keys)
- 7 tools: ingest, query, search, lint, create/update page, stats
- Markdown with YAML frontmatter
- Python 3.11+, MIT license

Architecture:
- SQLite FTS5 for keyword search
- all-MiniLM-L6-v2 for vector search (local, no network)
- Reciprocal Rank Fusion for hybrid ranking
- File locking for safe concurrent access
- Atomic writes + auto git commits

I built this following Karpathy's LLM Wiki pattern but made it shareable and provider-agnostic through MCP. The server handles data management; the LLM handles reasoning.

Looking for feedback, contributions, and ideas. The roadmap includes an Obsidian plugin (highest priority), browser extension, and REST API wrapper.

Repo: https://github.com/pisigmac/wikicapsule

---

## Reddit Post (r/LocalLLaMA)

**Title**: WikiCapsule — Local knowledge management through MCP (no cloud, fully open source)

**Body**:

Hey r/LocalLLaMA,

Built something you might appreciate: WikiCapsule is a fully local MCP server for managing knowledge wikis.

No cloud services needed. No API keys. No data leaves your machine.

Search uses:
- SQLite FTS5 (BM25 keyword search)
- sentence-transformers with all-MiniLM-L6-v2 (384-dim embeddings)
- Reciprocal Rank Fusion for hybrid ranking

Works with Ollama, local Claude, Cline, or any MCP client. Your wiki is just markdown files in a git repo.

GitHub: https://github.com/pisigmac/wikicapsule

Happy to answer questions or take feature requests.

---

## LinkedIn Post

**Title**: Launching WikiCapsule — Making AI Conversations Compound

**Body**:

Every day, millions of knowledge workers have rich, productive conversations with AI assistants. And every day, most of that knowledge evaporates when the session ends.

I built WikiCapsule to fix this.

It's an open-source MCP server that turns markdown files into a compounding knowledge base. Your AI assistant can read from it, write to it, search it, and keep it organized.

The result: knowledge that builds over time instead of disappearing.

Technical highlights:
- Model Context Protocol (MCP) for universal AI compatibility
- Git-backed for full version history
- Local hybrid search (BM25 + vector) with zero cloud dependencies
- Provider-agnostic: works with Claude, GPT-4, Gemini, and local models

If your team is exploring AI-augmented knowledge management, I'd love your feedback.

https://github.com/pisigmac/wikicapsule

#AI #MCP #KnowledgeManagement #OpenSource
