"""MCP resource implementations for WikiCapsule."""

from __future__ import annotations

import logging
import mcp.types as types
from pathlib import Path

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.wiki import WikiManager

logger = logging.getLogger(__name__)


def get_resource_list(config: WikiCapsuleConfig) -> list[types.Resource]:
    """Get the list of available resources."""
    resources: list[types.Resource] = []

    # Core wiki resources
    resources.append(
        types.Resource(
            uri="wiki://index.md",
            name="Wiki Index",
            description="Auto-maintained catalog of all wiki pages",
            mimeType="text/markdown",
        )
    )
    resources.append(
        types.Resource(
            uri="wiki://log.md",
            name="Wiki Log",
            description="Chronological append-only log of all operations",
            mimeType="text/markdown",
        )
    )
    resources.append(
        types.Resource(
            uri="wiki://WIKI.md",
            name="Wiki Schema (WIKI.md)",
            description="Provider-agnostic schema and configuration document",
            mimeType="text/markdown",
        )
    )

    return resources


def read_resource(uri: str, wiki: WikiManager, config: WikiCapsuleConfig) -> str:
    """Read a resource by URI and return its content.

    Args:
        uri: Resource URI (e.g., wiki://index.md)
        wiki: WikiManager instance
        config: Configuration

    Returns:
        Resource content as string
    """
    logger.debug("Reading resource: %s", uri)

    if not uri.startswith("wiki://"):
        raise ValueError(f"Invalid wiki resource URI: {uri}")

    path = uri[7:]  # Strip "wiki://"

    # Core resources
    if path == "index.md":
        # Sync index first to ensure freshness
        wiki.sync_index()
        page = wiki.get_page("index.md")
        if page:
            return page.raw_content
        return "# Wiki Index\n\n_No pages yet._"

    if path == "log.md":
        page = wiki.get_page("log.md")
        if page:
            return page.raw_content
        return "# Wiki Log\n\n_No activity yet._"

    if path == "WIKI.md":
        content = config.wiki_md_path.read_text(encoding="utf-8")
        return content

    # Wiki pages: wiki://wiki/{path}
    if path.startswith("wiki/"):
        page_path = path[5:]  # Strip "wiki/"
        page = wiki.get_page(page_path)
        if page:
            return page.raw_content
        raise FileNotFoundError(f"Wiki page not found: {page_path}")

    # Raw documents: wiki://raw/{path}
    if path.startswith("raw/"):
        raw_path = path[4:]  # Strip "raw/"
        content = wiki.get_raw(raw_path)
        if content is not None:
            return content
        raise FileNotFoundError(f"Raw document not found: {raw_path}")

    raise FileNotFoundError(f"Unknown wiki resource: {uri}")


def discover_wiki_pages(wiki: WikiManager, config: WikiCapsuleConfig) -> list[types.Resource]:
    """Dynamically discover all wiki pages as resources."""
    resources = get_resource_list(config)

    # Scan wiki directory for all .md files
    wiki_path = config.wiki_path
    if wiki_path.exists():
        for md_file in sorted(wiki_path.rglob("*.md")):
            rel_path = md_file.relative_to(wiki_path)
            uri = f"wiki://wiki/{rel_path}"
            name = str(rel_path.with_suffix(""))

            resources.append(
                types.Resource(
                    uri=str(uri),
                    name=name,
                    description=f"Wiki page: {name}",
                    mimeType="text/markdown",
                )
            )

    # Scan raw directory for all files
    raw_path = config.raw_path
    if raw_path.exists():
        for raw_file in sorted(raw_path.rglob("*")):
            if raw_file.is_file():
                rel_path = raw_file.relative_to(raw_path)
                uri = f"wiki://raw/{rel_path}"
                name = f"raw/{rel_path}"

                resources.append(
                    types.Resource(
                        uri=str(uri),
                        name=name,
                        description=f"Raw source: {name}",
                        mimeType="text/markdown" if raw_file.suffix == ".md" else "application/octet-stream",
                    )
                )

    logger.info("Discovered %d resources", len(resources))
    return resources
