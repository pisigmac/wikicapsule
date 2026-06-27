"""CLI interface for WikiCapsule — shell-native commands."""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.git_manager import GitManager
from wikicapsule.search import SearchEngine
from wikicapsule.wiki import WikiManager

logger = logging.getLogger(__name__)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new wiki capsule."""
    wiki_dir = Path(args.directory).expanduser().resolve()
    wiki_dir.mkdir(parents=True, exist_ok=True)

    config = WikiCapsuleConfig(wiki_dir=wiki_dir)
    config.save()

    # Initialize wiki structure
    wiki = WikiManager(config)

    print(f"Initialized wiki at: {wiki_dir}")
    print(f"Config: {config.config_file_path}")
    print("")
    print("Next steps:")
    print(f"  cd {wiki_dir}")
    print("  wikicapsule ingest ./my-article.md --type article")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Ingest a source document."""
    config = WikiCapsuleConfig.from_yaml()
    wiki = WikiManager(config)

    with GitManager(
        wiki_dir=config.wiki_dir,
        lock_timeout=config.wiki.lock_timeout_seconds,
        auto_commit=config.wiki.auto_commit,
    ) as git:
        result = wiki.ingest_source(
            source_path=args.source,
            source_type=args.type,
            tags=args.tags.split(",") if args.tags else [],
        )

        git.commit(
            operation="ingest",
            summary=f"Ingested {args.type}: {result['title']}",
        )

    print(f"Ingested: {result['title']}")
    print(f"  Source ID: {result['source_id']}")
    print(f"  Wiki page: {result['wiki_path']}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Query the wiki."""
    config = WikiCapsuleConfig.from_yaml()
    wiki = WikiManager(config)

    result = wiki.query(args.question)
    print(result)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search wiki pages."""
    config = WikiCapsuleConfig.from_yaml()
    wiki = WikiManager(config)

    results = wiki.search.search(
        query=args.query,
        limit=args.limit,
        search_type=args.type,
    )

    if not results:
        print(f"No results for: {args.query}")
        return 0

    print(f"Results for '{args.query}' ({args.type}):")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.title} ({r.path}) — {r.score:.3f}")
        if r.snippet:
            print(f"   {r.snippet[:120]}")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    """Lint the wiki."""
    config = WikiCapsuleConfig.from_yaml()
    wiki = WikiManager(config)

    issues = wiki.lint(scope=args.scope, auto_fix=args.auto_fix)

    if not issues:
        print("No issues found. Wiki is healthy.")
        return 0

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    print(f"Found {len(issues)} issues:")
    print(f"  {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")

    for issue in issues:
        prefix = f"[{issue.severity.upper()}]"
        page = f" ({issue.page_path})" if issue.page_path else ""
        print(f"  {prefix} {issue.category}: {issue.message}{page}")

    return 1 if errors else 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show wiki statistics."""
    config = WikiCapsuleConfig.from_yaml()
    wiki = WikiManager(config)

    stats = wiki.get_stats()
    search_stats = wiki.search.get_stats()

    print(f"Wiki: {config.wiki_dir}")
    print(f"  Total pages: {stats.total_pages}")
    print(f"    Entities: {stats.total_entities}")
    print(f"    Concepts: {stats.total_concepts}")
    print(f"    Sources: {stats.total_sources}")
    print(f"    Comparisons: {stats.total_comparisons}")
    print(f"    Explorations: {stats.total_explorations}")
    print(f"  Indexed pages: {search_stats['indexed_pages']}")
    print(f"  Search DB: {search_stats['db_size_mb']:.1f} MB")

    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """Show recent log entries."""
    config = WikiCapsuleConfig.from_yaml()
    log_path = config.wiki_path / "log.md"

    if not log_path.exists():
        print("No log entries yet.")
        return 0

    content = log_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Show last N entries
    tail = args.tail if hasattr(args, "tail") else 20
    print(f"Last {tail} log entries:")
    print("-" * 50)

    # Simple extraction of entries
    entry_lines = []
    current_entry = []
    for line in lines:
        if line.startswith("## ") and current_entry:
            entry_lines.append("\n".join(current_entry))
            current_entry = []
        current_entry.append(line)
    if current_entry:
        entry_lines.append("\n".join(current_entry))

    for entry in entry_lines[-tail:]:
        print(entry)
        print()

    return 0


def cmd_cat(args: argparse.Namespace) -> int:
    """Display a wiki page."""
    config = WikiCapsuleConfig.from_yaml()
    page_path = config.wiki_path / args.page

    if not page_path.exists():
        print(f"Page not found: {args.page}")
        return 1

    print(page_path.read_text(encoding="utf-8"))
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    """Open a wiki page in $EDITOR."""
    config = WikiCapsuleConfig.from_yaml()
    page_path = config.wiki_path / args.page

    editor = os.environ.get("EDITOR", "vim")
    subprocess.run([editor, str(page_path)], check=False)
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="wikicapsule",
        description="WikiCapsule — Knowledge management for LLMs",
    )
    parser.add_argument(
        "--wiki-dir",
        type=str,
        default=".",
        help="Wiki directory (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_p = subparsers.add_parser("init", help="Initialize a new wiki capsule")
    init_p.add_argument("directory", nargs="?", default=".", help="Directory to initialize")
    init_p.set_defaults(func=cmd_init)

    # ingest
    ingest_p = subparsers.add_parser("ingest", help="Ingest a source document")
    ingest_p.add_argument("source", help="Path to source file")
    ingest_p.add_argument("--type", default="article", help="Source type")
    ingest_p.add_argument("--tags", default="", help="Comma-separated tags")
    ingest_p.set_defaults(func=cmd_ingest)

    # query
    query_p = subparsers.add_parser("query", help="Query the wiki")
    query_p.add_argument("question", help="Question to answer")
    query_p.set_defaults(func=cmd_query)

    # search
    search_p = subparsers.add_parser("search", help="Search wiki pages")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--limit", type=int, default=10, help="Max results")
    search_p.add_argument("--type", default="hybrid", choices=["bm25", "vector", "hybrid"])
    search_p.set_defaults(func=cmd_search)

    # lint
    lint_p = subparsers.add_parser("lint", help="Health-check the wiki")
    lint_p.add_argument("--scope", default="quick", choices=["quick", "full"])
    lint_p.add_argument("--auto-fix", action="store_true", help="Auto-fix issues")
    lint_p.set_defaults(func=cmd_lint)

    # stats
    stats_p = subparsers.add_parser("stats", help="Show wiki statistics")
    stats_p.set_defaults(func=cmd_stats)

    # log
    log_p = subparsers.add_parser("log", help="Show operation log")
    log_p.add_argument("--tail", type=int, default=20, help="Number of entries")
    log_p.set_defaults(func=cmd_log)

    # cat
    cat_p = subparsers.add_parser("cat", help="Display a wiki page")
    cat_p.add_argument("page", help="Page path (e.g., entities/topic.md)")
    cat_p.set_defaults(func=cmd_cat)

    # edit
    edit_p = subparsers.add_parser("edit", help="Edit a wiki page")
    edit_p.add_argument("page", help="Page path")
    edit_p.set_defaults(func=cmd_edit)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
