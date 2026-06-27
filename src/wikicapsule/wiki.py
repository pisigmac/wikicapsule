"""Wiki directory operations — CRUD, index/log maintenance, directory structure."""

from __future__ import annotations

import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.git_manager import GitManager
from wikicapsule.markdown import (
    create_page_content,
    get_content_preview,
    parse_page,
    render_page_to_markdown,
)
from wikicapsule.models import (
    Frontmatter,
    LintIssue,
    LogEntry,
    PageStatus,
    PageType,
    WikiPage,
    WikiStats,
)
from wikicapsule.search import SearchEngine

logger = logging.getLogger(__name__)

WIKI_SCHEMA_TEMPLATE = """# WikiCapsule Schema

> This document describes the structure and conventions of this wiki. It's provider-agnostic — any AI agent or human can read it to understand how this knowledge base works.

## Directory Structure

```
wiki/
├── index.md          # Auto-maintained catalog of all pages
├── log.md            # Auto-maintained chronological log
├── overview.md       # High-level synthesis of all knowledge
├── entities/         # People, organizations, products
├── concepts/         # Ideas, theories, terms
├── sources/          # One page per ingested source
├── comparisons/      # Comparison tables and decision matrices
└── explorations/     # Answers to past queries, filed here
```

## Page Naming Rules

- Use **kebab-case** for all filenames: `my-page-name.md`
- Organize by type: `entities/person-name.md`, `concepts/term-name.md`
- Keep paths flat — max 2 levels deep
- Use descriptive names: prefer `transformer-architecture.md` over `transformers.md`

## Frontmatter Schema

Every page must have YAML frontmatter:

```yaml
---
title: "Human-Readable Title"
type: entity|concept|source|comparison|exploration
tags: [tag1, tag2]
sources: [source-id-1, source-id-2]
created: 2024-01-01T00:00:00
updated: 2024-01-01T00:00:00
status: draft|review|stable
---
```

Fields:
- **title** (required): Human-readable page title
- **type** (required): Page category
- **tags** (optional): Topic tags for filtering
- **sources** (optional): IDs of source documents this page references
- **status** (optional): Content maturity level

## Ingest Workflow (7 Steps)

1. Read and understand the source material
2. Discuss key insights with the user (if interactive)
3. Write a summary page in `sources/`
4. Update or create relevant entity pages in `entities/`
5. Update or create relevant concept pages in `concepts/`
6. Update `index.md` with new entries
7. Append entry to `log.md`

## Query Workflow (5 Steps)

1. Read `index.md` to understand wiki contents
2. Search for relevant pages using `wiki_search`
3. Read the most relevant pages
4. Synthesize an answer with citations
5. Optionally file the answer as a new exploration page

## Lint Checklist (10 Items)

1. Orphan pages: Pages with no incoming wikilinks for 30+ days
2. Stale claims: Pages not updated since their sources changed
3. Contradictions: Incompatible statements across pages
4. Missing pages: Wikilinks pointing to non-existent pages
5. Broken links: External URLs that may be dead
6. Empty pages: Pages with no meaningful content
7. Untagged pages: Pages missing relevant tags
8. Draft rot: Pages in draft status for too long
9. Duplicate coverage: Multiple pages covering the same topic
10. Index drift: `index.md` out of sync with actual pages

## Cross-Reference Conventions

Use wikilink syntax for internal links:
- `[[Page Name]]` — Link to another wiki page
- The page resolver is case-insensitive and hyphen-tolerant
- Broken wikilinks (pointing to non-existent pages) are flagged by `wiki_lint`

## Contradiction Flagging

When you find conflicting information across pages, flag it:

```markdown
> ⚠️ **Contradiction**: Page A says X, but Page B says Y.
> Source: [source-id], Status: unresolved
```

## Log Entry Format

```markdown
## YYYY-MM-DD HH:MM — operation: summary

- Operation: ingest|query|lint|search|create|update
- Details: any relevant context
```
"""

INDEX_TEMPLATE = """# Wiki Index

> Auto-maintained catalog of all pages. Last updated: {timestamp}

## Overview

{overview}

## Pages by Category

### Entities ({entity_count})

{entity_list}

### Concepts ({concept_count})

{concept_list}

### Sources ({source_count})

{source_list}

### Comparisons ({comparison_count})

{comparison_list}

### Explorations ({exploration_count})

{exploration_list}

## Recent Activity

{recent_activity}
"""

LOG_TEMPLATE = """# Wiki Log

> Chronological record of all operations. Append-only.

## Entries

{entries}

---

*Log started: {start_date}*
"""

EMPTY_OVERVIEW = """# Wiki Overview

This wiki is empty. Start by ingesting a source document.

## Quick Start

1. Ingest your first source: Use the `wiki_ingest` tool with a file path or URL
2. Explore the wiki: Use `wiki_query` to ask questions
3. Keep it healthy: Run `wiki_lint` periodically
"""


class WikiManager:
    """Manages the wiki directory structure, pages, and auto-generated files."""

    def __init__(self, config: WikiCapsuleConfig) -> None:
        self.config = config
        self.search = SearchEngine(
            db_path=config.search_db_path,
            model_name=config.wiki.search.vector_model,
            hybrid_alpha=config.wiki.search.hybrid_alpha,
        )
        self._ensure_directory_structure()

    def _ensure_directory_structure(self) -> None:
        """Create the wiki directory structure if it doesn't exist."""
        dirs = [
            self.config.raw_path / "articles",
            self.config.raw_path / "papers",
            self.config.raw_path / "books",
            self.config.raw_path / "transcripts",
            self.config.raw_path / "assets",
            self.config.wiki_path / "entities",
            self.config.wiki_path / "concepts",
            self.config.wiki_path / "sources",
            self.config.wiki_path / "comparisons",
            self.config.wiki_path / "explorations",
            self.config.dot_wikicapsule_path,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # Create WIKI.md if missing
        if not self.config.wiki_md_path.exists():
            self._atomic_write(self.config.wiki_md_path, WIKI_SCHEMA_TEMPLATE)
            logger.info("Created WIKI.md schema document")

        # Create initial overview.md if missing
        overview_path = self.config.wiki_path / "overview.md"
        if not overview_path.exists():
            self._atomic_write(overview_path, EMPTY_OVERVIEW)
            logger.info("Created initial overview.md")

        # Save default config if missing
        if not self.config.config_file_path.exists():
            self.config.save()
            logger.info("Created default config.yaml")

    def _atomic_write(self, path: Path, content: str) -> None:
        """Write content atomically using temp file + rename."""
        path = path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            shutil.move(tmp_path, str(path))
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def _read_page_file(self, path: str) -> WikiPage | None:
        """Read and parse a wiki page by relative path."""
        full_path = self.config.wiki_path / path
        if not full_path.exists():
            return None
        try:
            raw = full_path.read_text(encoding="utf-8")
            return parse_page(path, raw)
        except Exception as e:
            logger.error("Failed to parse page '%s': %s", path, e)
            return None

    def _write_page_file(self, path: str, content: str) -> None:
        """Write content to a wiki page file."""
        full_path = self.config.wiki_path / path
        self._atomic_write(full_path, content)

    def _list_pages(self, subdir: str | None = None) -> list[str]:
        """List all page paths in the wiki, optionally filtered by subdirectory."""
        base = self.config.wiki_path
        if subdir:
            base = base / subdir

        if not base.exists():
            return []

        pages = []
        for f in base.rglob("*.md"):
            rel = f.relative_to(self.config.wiki_path)
            pages.append(str(rel))
        return sorted(pages)

    def page_exists(self, path: str) -> bool:
        """Check if a wiki page exists."""
        return (self.config.wiki_path / path).exists()

    def create_page(
        self,
        path: str,
        content: str,
        tags: list[str] | None = None,
    ) -> str:
        """Create a new wiki page.

        Returns:
            The full page content written
        """
        if self.page_exists(path):
            raise FileExistsError(f"Page already exists: {path}")

        title = None
        # Try to extract title from content H1
        lines = content.strip().split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        if not title:
            title = path.replace("-", " ").replace(".md", "").title()

        # Infer type from path
        page_type = _infer_page_type(path)

        full_content = create_page_content(
            title=title,
            page_type=page_type,
            content=content,
            tags=tags or [],
        )

        self._write_page_file(path, full_content)

        # Index for search
        self.search.index_page(
            path=path,
            title=title,
            content=content,
            page_type=page_type.value,
            tags=tags or [],
        )

        logger.info("Created page: %s", path)
        return full_content

    def update_page(self, path: str, content: str, reason: str = "") -> str:
        """Update an existing wiki page.

        Returns:
            The full page content written
        """
        existing = self._read_page_file(path)
        if not existing:
            raise FileNotFoundError(f"Page not found: {path}")

        # Try to extract title from new content
        title = existing.frontmatter.title
        lines = content.strip().split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Preserve frontmatter fields, update content
        fm = existing.frontmatter
        fm.title = title
        fm.status = PageStatus.REVIEW

        full_content = create_page_content(
            title=fm.title,
            page_type=fm.type,
            content=content,
            tags=fm.tags,
            sources=fm.sources,
        )

        self._write_page_file(path, full_content)

        # Re-index
        self.search.index_page(
            path=path,
            title=fm.title,
            content=content,
            page_type=fm.type.value,
            tags=fm.tags,
            sources=fm.sources,
        )

        logger.info("Updated page: %s (%s)", path, reason)
        return full_content

    def get_page(self, path: str) -> WikiPage | None:
        """Read a wiki page by path."""
        return self._read_page_file(path)

    def get_raw(self, path: str) -> str | None:
        """Read a raw source document by path."""
        full_path = self.config.raw_path / path
        if not full_path.exists():
            return None
        try:
            return full_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Failed to read raw '%s': %s", path, e)
            return None

    def ingest_source(
        self,
        source_path: str,
        source_type: str,
        tags: list[str] | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Ingest a source document into the wiki.

        Returns:
            Dict with paths of created/updated files
        """
        import uuid

        source_id = str(uuid.uuid4())[:8]

        # Determine storage path
        type_dir = {
            "article": "articles",
            "paper": "papers",
            "book_chapter": "books",
            "transcript": "transcripts",
            "note": "notes",
        }.get(source_type, "articles")

        # Get content
        if content:
            source_content = content
            title = _extract_title(source_content) or f"Untitled {source_type}"
        else:
            src_path = Path(source_path).expanduser().resolve()
            if src_path.exists():
                source_content = src_path.read_text(encoding="utf-8")
                title = _extract_title(source_content) or src_path.stem
            else:
                source_content = f"# Source: {source_path}\n\n(Content not available)"
                title = source_path

        # Store raw
        raw_filename = f"{type_dir}/{source_id}-{title.lower().replace(' ', '-').replace('/', '-')[:50]}.md"
        raw_filename = raw_filename.replace("--", "-")
        raw_path = self.config.raw_path / raw_filename
        self._atomic_write(raw_path, source_content)

        # Create source page
        source_wiki_path = f"sources/{source_id}.md"
        source_wiki_content = f"""# {title}

> Source type: {source_type} | ID: `{source_id}`

## Summary

<!-- Add a brief summary of the source here -->

## Key Points

<!-- Extract key points from the source -->

## Full Content

{source_content[:self.config.ingest.summary_max_length] if len(source_content) > self.config.ingest.summary_max_length else source_content}
"""

        if len(source_content) > self.config.ingest.summary_max_length:
            source_wiki_content += "\n\n> (Content truncated — see raw source for full text)\n"

        self.create_page(
            path=source_wiki_path,
            content=source_wiki_content,
            tags=[source_type] + (tags or []),
        )

        # Index source
        self.search.add_source(
            source_id=source_id,
            path=raw_filename,
            title=title,
            source_type=source_type,
        )

        # Update log
        self._append_log("ingest", f"Ingested {source_type}: {title}", {"source_id": source_id})

        # Update index
        self._rebuild_index()

        return {
            "source_id": source_id,
            "raw_path": raw_filename,
            "wiki_path": source_wiki_path,
            "title": title,
        }

    def query(self, question: str) -> str:
        """Query the wiki — returns guidance on how to answer (the LLM does the synthesis)."""
        results = self.search.search_hybrid(question, limit=10)

        if not results:
            return (
                f"No wiki pages found for: '{question}'\n\n"
                "Try ingesting some sources first, or rephrase your question."
            )

        lines = [f"# Query: {question}\n", f"Found {len(results)} relevant pages:\n"]

        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.title}** (`{r.path}`)")
            if r.snippet:
                lines.append(f"   > {r.snippet[:150]}")
            lines.append("")

        lines.append("\nTo answer this question:")
        lines.append("1. Read the relevant pages above using `wiki://wiki/{{path}}`")
        lines.append("2. Synthesize an answer with citations to specific pages")
        lines.append("3. Optionally file your answer as a new exploration page")

        return "\n".join(lines)

    def lint(self, scope: str = "quick", auto_fix: bool = False) -> list[LintIssue]:
        """Run lint checks on the wiki.

        Returns:
            List of found issues
        """
        issues: list[LintIssue] = []
        pages = self._list_all_pages()

        # 1. Check for orphan pages
        all_wikilinks: set[str] = set()
        page_map: dict[str, WikiPage] = {}

        for p in pages:
            wp = self._read_page_file(p)
            if wp:
                page_map[p] = wp
                all_wikilinks.update(wp.wikilinks)

        # Build title -> path mapping for wikilink resolution
        title_to_path: dict[str, str] = {}
        for path, wp in page_map.items():
            title_to_path[wp.frontmatter.title.lower()] = path
            title_to_path[Path(path).stem.lower()] = path

        # Orphan check: pages not referenced by any wikilink
        if scope == "full":
            referenced_paths = set()
            for link in all_wikilinks:
                link_lower = link.lower()
                if link_lower in title_to_path:
                    referenced_paths.add(title_to_path[link_lower])

            for path, wp in page_map.items():
                if wp.frontmatter.type in (PageType.INDEX, PageType.LOG, PageType.OVERVIEW):
                    continue
                if path not in referenced_paths:
                    issues.append(
                        LintIssue(
                            severity="warning",
                            category="orphan",
                            message=f"Page '{wp.frontmatter.title}' has no incoming wikilinks",
                            page_path=path,
                            suggestion=f"Link to [[{wp.frontmatter.title}]] from related pages",
                        )
                    )

        # 2. Check for broken wikilinks
        for path, wp in page_map.items():
            for link in wp.wikilinks:
                link_lower = link.lower()
                exists = False
                # Check as title
                if link_lower in title_to_path:
                    exists = True
                # Check as path stem
                for p in pages:
                    if Path(p).stem.lower() == link_lower:
                        exists = True
                        break
                if not exists:
                    issues.append(
                        LintIssue(
                            severity="warning",
                            category="missing",
                            message=f"Wikilink [[{link}]] on '{wp.frontmatter.title}' points to non-existent page",
                            page_path=path,
                            suggestion=f"Create page for [[{link}]] or fix the link",
                        )
                    )

        # 3. Check for empty pages
        for path, wp in page_map.items():
            content_stripped = wp.content.strip()
            if len(content_stripped) < 50:
                issues.append(
                    LintIssue(
                        severity="info",
                        category="empty",
                        message=f"Page '{wp.frontmatter.title}' has very little content",
                        page_path=path,
                        suggestion="Add more content or remove the page",
                    )
                )

        # 4. Check for untagged pages
        for path, wp in page_map.items():
            if wp.frontmatter.type in (PageType.INDEX, PageType.LOG):
                continue
            if not wp.frontmatter.tags:
                issues.append(
                    LintIssue(
                        severity="info",
                        category="orphan",
                        message=f"Page '{wp.frontmatter.title}' has no tags",
                        page_path=path,
                        suggestion="Add relevant tags to improve discoverability",
                    )
                )

        # 5. Draft rot
        for path, wp in page_map.items():
            if wp.frontmatter.status == PageStatus.DRAFT:
                issues.append(
                    LintIssue(
                        severity="info",
                        category="stale",
                        message=f"Page '{wp.frontmatter.title}' is still in draft status",
                        page_path=path,
                        suggestion="Review and mark as 'review' or 'stable'",
                    )
                )

        # Update log
        if issues:
            self._append_log(
                "lint",
                f"Found {len(issues)} issues ({scope} scope)",
                {"issue_count": len(issues), "auto_fix": auto_fix},
            )

        return issues

    def get_stats(self) -> WikiStats:
        """Get comprehensive wiki statistics."""
        pages = self._list_all_pages()
        stats = WikiStats(total_pages=len(pages))

        status_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}

        for p in pages:
            wp = self._read_page_file(p)
            if not wp:
                continue

            status = wp.frontmatter.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            for tag in wp.frontmatter.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            t = wp.frontmatter.type
            if t == PageType.ENTITY:
                stats.total_entities += 1
            elif t == PageType.CONCEPT:
                stats.total_concepts += 1
            elif t == PageType.SOURCE:
                stats.total_sources += 1
            elif t == PageType.COMPARISON:
                stats.total_comparisons += 1
            elif t == PageType.EXPLORATION:
                stats.total_explorations += 1

        stats.pages_by_status = status_counts
        stats.pages_by_tag = tag_counts

        # Search index stats
        search_stats = self.search.get_stats()
        stats.index_size_mb = search_stats["db_size_mb"]

        return stats

    def _list_all_pages(self) -> list[str]:
        """List all wiki pages excluding auto-generated ones."""
        all_pages = self._list_pages()
        # Exclude auto-generated root files
        auto_files = {"index.md", "log.md", "overview.md"}
        return [p for p in all_pages if p not in auto_files]

    def _rebuild_index(self) -> None:
        """Rebuild the index.md page from current wiki contents."""
        pages = self._list_all_pages()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Group by type
        entities = [p for p in pages if p.startswith("entities/")]
        concepts_list = [p for p in pages if p.startswith("concepts/")]
        sources_list = [p for p in pages if p.startswith("sources/")]
        comparisons_list = [p for p in pages if p.startswith("comparisons/")]
        explorations_list = [p for p in pages if p.startswith("explorations/")]

        def _format_list(paths: list[str]) -> str:
            if not paths:
                return "_No pages yet._"
            lines = []
            for p in sorted(paths):
                wp = self._read_page_file(p)
                title = wp.frontmatter.title if wp else Path(p).stem
                tags = ", ".join(f"`{t}`" for t in (wp.frontmatter.tags if wp else []))
                tag_str = f" — {tags}" if tags else ""
                lines.append(f"- [[{title}]] (`{p}`){tag_str}")
            return "\n".join(lines)

        # Get overview
        overview = "This wiki contains knowledge from various sources."
        overview_page = self._read_page_file("overview.md")
        if overview_page:
            overview = get_content_preview(overview_page.content, 300)

        # Recent activity from search log
        recent = "No recent activity."

        index_content = INDEX_TEMPLATE.format(
            timestamp=now,
            overview=overview,
            entity_count=len(entities),
            concept_count=len(concepts_list),
            source_count=len(sources_list),
            comparison_count=len(comparisons_list),
            exploration_count=len(explorations_list),
            entity_list=_format_list(entities),
            concept_list=_format_list(concepts_list),
            source_list=_format_list(sources_list),
            comparison_list=_format_list(comparisons_list),
            exploration_list=_format_list(explorations_list),
            recent_activity=recent,
        )

        self._write_page_file("index.md", index_content)
        self.search.index_page(path="index.md", title="Wiki Index", content=index_content, page_type="index")

    def _append_log(self, operation: str, summary: str, details: dict | None = None) -> None:
        """Append an entry to log.md."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"## {now} — {operation}: {summary}\n\n"
        if details:
            for key, value in details.items():
                entry += f"- **{key}**: {value}\n"
            entry += "\n"

        log_path = self.config.wiki_path / "log.md"
        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")
            # Insert after header
            lines = existing.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## Entries"):
                    insert_idx = i + 1
                    break
            lines.insert(insert_idx, entry)
            new_content = "\n".join(lines)
        else:
            start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            new_content = LOG_TEMPLATE.format(entries=entry, start_date=start_date)

        self._write_page_file("log.md", new_content)
        self.search.add_log(operation, summary, details)

    def sync_index(self) -> None:
        """Force rebuild of index.md."""
        self._rebuild_index()


def _infer_page_type(path: str) -> PageType:
    """Infer page type from path."""
    if path.startswith("entities/"):
        return PageType.ENTITY
    if path.startswith("concepts/"):
        return PageType.CONCEPT
    if path.startswith("sources/"):
        return PageType.SOURCE
    if path.startswith("comparisons/"):
        return PageType.COMPARISON
    if path.startswith("explorations/"):
        return PageType.EXPLORATION
    return PageType.CONCEPT


def _extract_title(content: str) -> str | None:
    """Extract title from first H1 heading."""
    for line in content.strip().split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return None

import os
