"""MCP tool implementations for WikiCapsule."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.git_manager import GitManager
from wikicapsule.models import (
    IngestRequest,
    LintRequest,
    PageCreateRequest,
    PageUpdateRequest,
    QueryRequest,
    SearchRequest,
)
from wikicapsule.wiki import WikiManager

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, wiki: WikiManager, config: WikiCapsuleConfig) -> None:
    """Register all MCP tools with the server."""

    @mcp.tool()
    def wiki_ingest(
        source_path: str,
        source_type: str,
        tags: list[str] | None = None,
    ) -> str:
        """Ingest a new source document into the wiki.

        Args:
            source_path: Path to source file or URL
            source_type: Type of source (article/paper/book_chapter/transcript/note)
            tags: Optional tags to apply

        Returns:
            Summary of the ingest operation
        """
        try:
            req = IngestRequest(
                source_path=source_path,
                source_type=source_type,
                tags=tags or [],
            )
        except ValueError as e:
            return f"Invalid request: {e}"

        with GitManager(
            wiki_dir=config.wiki_dir,
            lock_timeout=config.wiki.lock_timeout_seconds,
            auto_commit=config.wiki.auto_commit,
        ) as git:
            try:
                result = wiki.ingest_source(
                    source_path=req.source_path,
                    source_type=req.source_type,
                    tags=req.tags,
                    content=req.content,
                )

                # Commit changes
                git.commit(
                    operation="ingest",
                    summary=f"Ingested {req.source_type}: {result['title']}",
                    files=[
                        config.raw_path / result["raw_path"],
                        config.wiki_path / result["wiki_path"],
                        config.wiki_path / "index.md",
                        config.wiki_path / "log.md",
                    ],
                )

                return (
                    f"Ingested '{result['title']}'\n"
                    f"- Source ID: `{result['source_id']}`\n"
                    f"- Raw: `{result['raw_path']}`\n"
                    f"- Wiki page: `{result['wiki_path']}`\n"
                    f"- Tags: {', '.join(req.tags) if req.tags else 'none'}"
                )
            except Exception as e:
                logger.error("Ingest failed: %s", e)
                return f"Ingest failed: {e}"

    @mcp.tool()
    def wiki_query(
        question: str,
        output_format: str = "markdown",
    ) -> str:
        """Query the wiki and get relevant pages to synthesize an answer.

        Args:
            question: Your question about the wiki contents
            output_format: Desired format (markdown/table/slides/chart)

        Returns:
            Search results and guidance for synthesizing an answer
        """
        try:
            req = QueryRequest(question=question, output_format=output_format)
        except ValueError as e:
            return f"Invalid request: {e}"

        try:
            return wiki.query(req.question)
        except Exception as e:
            logger.error("Query failed: %s", e)
            return f"Query failed: {e}"

    @mcp.tool()
    def wiki_search(
        query: str,
        limit: int = 10,
        type: str = "hybrid",  # noqa: A002
    ) -> str:
        """Search wiki pages using BM25, vector, or hybrid search.

        Args:
            query: Search query string
            limit: Maximum results (1-100)
            type: Search type — bm25, vector, or hybrid

        Returns:
            Search results with relevance scores and snippets
        """
        try:
            req = SearchRequest(query=query, limit=limit, type=type)
        except ValueError as e:
            return f"Invalid request: {e}"

        try:
            results = wiki.search.search(req.query, req.limit, req.search_type)

            if not results:
                return f"No results found for '{req.query}'"

            lines = [f"# Search: '{req.query}' ({req.search_type})\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r.title}** (`{r.path}`) — score: {r.score:.3f}")
                if r.snippet:
                    lines.append(f"   > {r.snippet[:200]}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            logger.error("Search failed: %s", e)
            return f"Search failed: {e}"

    @mcp.tool()
    def wiki_lint(
        scope: str = "quick",
        auto_fix: bool = False,
    ) -> str:
        """Health-check the wiki for issues.

        Args:
            scope: 'quick' (basic checks) or 'full' (comprehensive)
            auto_fix: Whether to automatically fix issues where possible

        Returns:
            Lint report with found issues and suggestions
        """
        try:
            req = LintRequest(scope=scope, auto_fix=auto_fix)
        except ValueError as e:
            return f"Invalid request: {e}"

        try:
            issues = wiki.lint(scope=req.scope, auto_fix=req.auto_fix)

            if not issues:
                return f"Lint ({req.scope}): No issues found. Wiki is healthy."

            # Group by severity
            errors = [i for i in issues if i.severity == "error"]
            warnings = [i for i in issues if i.severity == "warning"]
            infos = [i for i in issues if i.severity == "info"]

            lines = [f"# Lint Report ({req.scope})\n"]
            lines.append(f"Found {len(issues)} issues: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info\n")

            for sev, items in [("Errors", errors), ("Warnings", warnings), ("Info", infos)]:
                if items:
                    lines.append(f"## {sev}")
                    for issue in items:
                        page_ref = f" (`{issue.page_path}`)" if issue.page_path else ""
                        lines.append(f"- **{issue.category}**: {issue.message}{page_ref}")
                        if issue.suggestion:
                            lines.append(f"  - *Suggestion: {issue.suggestion}*")
                    lines.append("")

            return "\n".join(lines)
        except Exception as e:
            logger.error("Lint failed: %s", e)
            return f"Lint failed: {e}"

    @mcp.tool()
    def wiki_create_page(
        path: str,
        content: str,
        tags: list[str] | None = None,
    ) -> str:
        """Create a new wiki page.

        Args:
            path: Wiki page path (e.g., 'entities/new-topic.md')
            content: Markdown content for the page
            tags: Optional tags

        Returns:
            Confirmation with the created page path
        """
        try:
            req = PageCreateRequest(path=path, content=content, tags=tags or [])
        except ValueError as e:
            return f"Invalid request: {e}"

        with GitManager(
            wiki_dir=config.wiki_dir,
            lock_timeout=config.wiki.lock_timeout_seconds,
            auto_commit=config.wiki.auto_commit,
        ) as git:
            try:
                wiki.create_page(path=req.path, content=req.content, tags=req.tags)

                git.commit(
                    operation="create",
                    summary=f"Created page {req.path}",
                    files=[config.wiki_path / req.path, config.wiki_path / "index.md"],
                )

                return f"Created page: `{req.path}`\n- Tags: {', '.join(req.tags) if req.tags else 'none'}"
            except FileExistsError:
                return f"Page already exists: `{req.path}`. Use wiki_update_page to modify it."
            except Exception as e:
                logger.error("Create page failed: %s", e)
                return f"Create page failed: {e}"

    @mcp.tool()
    def wiki_update_page(
        path: str,
        content: str,
        reason: str,
    ) -> str:
        """Update an existing wiki page.

        Args:
            path: Wiki page path (e.g., 'entities/topic.md')
            content: New markdown content (replaces existing)
            reason: Why this update is being made

        Returns:
            Confirmation with the updated page path
        """
        try:
            req = PageUpdateRequest(path=path, content=content, reason=reason)
        except ValueError as e:
            return f"Invalid request: {e}"

        with GitManager(
            wiki_dir=config.wiki_dir,
            lock_timeout=config.wiki.lock_timeout_seconds,
            auto_commit=config.wiki.auto_commit,
        ) as git:
            try:
                wiki.update_page(path=req.path, content=req.content, reason=req.reason)

                git.commit(
                    operation="update",
                    summary=f"Updated {req.path}: {req.reason}",
                    files=[config.wiki_path / req.path, config.wiki_path / "log.md"],
                )

                return f"Updated page: `{req.path}`\n- Reason: {req.reason}"
            except FileNotFoundError:
                return f"Page not found: `{req.path}`. Use wiki_create_page to create it."
            except Exception as e:
                logger.error("Update page failed: %s", e)
                return f"Update page failed: {e}"

    @mcp.tool()
    def wiki_get_stats() -> str:
        """Get wiki statistics.

        Returns:
            Formatted statistics about the wiki
        """
        try:
            stats = wiki.get_stats()
            search_stats = wiki.search.get_stats()

            lines = ["# Wiki Statistics\n"]
            lines.append(f"- **Total pages**: {stats.total_pages}")
            lines.append(f"  - Entities: {stats.total_entities}")
            lines.append(f"  - Concepts: {stats.total_concepts}")
            lines.append(f"  - Sources: {stats.total_sources}")
            lines.append(f"  - Comparisons: {stats.total_comparisons}")
            lines.append(f"  - Explorations: {stats.total_explorations}")
            lines.append("")
            lines.append(f"- **Indexed pages**: {search_stats['indexed_pages']}")
            lines.append(f"- **Search DB size**: {search_stats['db_size_mb']:.1f} MB")
            lines.append("")

            if stats.pages_by_status:
                lines.append("## Pages by Status")
                for status, count in sorted(stats.pages_by_status.items()):
                    lines.append(f"- {status}: {count}")
                lines.append("")

            if stats.pages_by_tag:
                lines.append("## Top Tags")
                top_tags = sorted(stats.pages_by_tag.items(), key=lambda x: x[1], reverse=True)[:10]
                for tag, count in top_tags:
                    lines.append(f"- `{tag}`: {count}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            logger.error("Get stats failed: %s", e)
            return f"Get stats failed: {e}"
