"""Markdown parser for wiki pages — frontmatter, wikilinks, and content extraction."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import frontmatter
from markdown_it import MarkdownIt

from wikicapsule.models import Frontmatter, PageStatus, PageType, WikiPage

logger = logging.getLogger(__name__)

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_DELIM = "---\n"

_md = MarkdownIt("commonmark", {"html": False})


def parse_page(path: str, raw_content: str) -> WikiPage:
    """Parse a wiki page from raw markdown content.

    Args:
        path: Relative path in wiki/ directory (e.g., 'entities/karpathy.md')
        raw_content: Full markdown content including frontmatter

    Returns:
        Parsed WikiPage with frontmatter, content, and wikilinks
    """
    # Parse frontmatter using python-frontmatter
    post = frontmatter.loads(raw_content)

    # Build frontmatter model
    fm_data = post.metadata or {}
    frontmatter_obj = Frontmatter(
        title=fm_data.get("title", _path_to_title(path)),
        type=_parse_page_type(fm_data.get("type", "concept")),
        tags=_ensure_list(fm_data.get("tags", [])),
        sources=_ensure_list(fm_data.get("sources", [])),
        status=_parse_page_status(fm_data.get("status", "draft")),
    )

    # Extract wikilinks from content
    content = post.content or ""
    wikilinks = extract_wikilinks(content)

    return WikiPage(
        path=path,
        frontmatter=frontmatter_obj,
        content=content,
        raw_content=raw_content,
        wikilinks=wikilinks,
    )


def extract_wikilinks(content: str) -> list[str]:
    """Extract all [[Page Name]] wikilink references from content."""
    return [match.group(1).strip() for match in WIKILINK_RE.finditer(content)]


def render_page_to_markdown(page: WikiPage) -> str:
    """Render a WikiPage back to markdown string with frontmatter."""
    fm_dict: dict[str, Any] = {
        "title": page.frontmatter.title,
        "type": page.frontmatter.type.value,
        "tags": page.frontmatter.tags,
        "sources": page.frontmatter.sources,
        "status": page.frontmatter.status.value,
    }

    # Clean up empty lists for cleaner output
    fm_dict = {k: v for k, v in fm_dict.items() if v}

    post = frontmatter.Post(page.content, **fm_dict)
    return frontmatter.dumps(post)


def create_page_content(
    title: str,
    page_type: PageType,
    content: str,
    tags: list[str] | None = None,
    sources: list[str] | None = None,
) -> str:
    """Create a new wiki page with proper frontmatter.

    Args:
        title: Human-readable page title
        page_type: Category of the page
        content: Markdown body content
        tags: Optional list of tags
        sources: Optional list of source IDs

    Returns:
        Complete markdown string with YAML frontmatter
    """
    fm: dict[str, Any] = {
        "title": title,
        "type": page_type.value,
    }
    if tags:
        fm["tags"] = tags
    if sources:
        fm["sources"] = sources

    post = frontmatter.Post(content.strip(), **fm)
    return frontmatter.dumps(post)


def extract_title_from_content(content: str) -> str | None:
    """Try to extract a title from the first H1 heading in content."""
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def get_content_preview(content: str, max_length: int = 200) -> str:
    """Get a text preview of content, stripped of markdown syntax."""
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", " ", content)
    # Remove inline code
    text = re.sub(r"`[^`]+`", " ", text)
    # Remove headings
    text = re.sub(r"#{1,6}\s+", " ", text)
    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove wikilinks but keep text
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Remove emphasis markers
    text = re.sub(r"[*_]{1,2}", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def _path_to_title(path: str) -> str:
    """Derive a title from a wiki path."""
    # Remove directory and extension
    name = Path(path).stem
    # Convert kebab-case to Title Case
    return name.replace("-", " ").replace("_", " ").title()


def _parse_page_type(value: Any) -> PageType:
    """Parse a page type string to enum."""
    if isinstance(value, PageType):
        return value
    try:
        return PageType(str(value).lower())
    except ValueError:
        logger.warning("Unknown page type '%s', defaulting to concept", value)
        return PageType.CONCEPT


def _parse_page_status(value: Any) -> PageStatus:
    """Parse a page status string to enum."""
    if isinstance(value, PageStatus):
        return value
    try:
        return PageStatus(str(value).lower())
    except ValueError:
        logger.warning("Unknown page status '%s', defaulting to draft", value)
        return PageStatus.DRAFT


def _ensure_list(value: Any) -> list[str]:
    """Ensure a value is a list of strings."""
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]
