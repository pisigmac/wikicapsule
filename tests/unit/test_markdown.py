"""Unit tests for markdown parser."""

from __future__ import annotations

from wikicapsule.markdown import (
    create_page_content,
    extract_wikilinks,
    get_content_preview,
    parse_page,
)
from wikicapsule.models import PageType, WikiPage


class TestParsePage:
    """Tests for parse_page function."""

    def test_parse_with_frontmatter(self) -> None:
        raw = """---
title: Test Page
type: entity
tags: [ml, ai]
---

# Test Page

This is a test page with a [[Link]] to another page.
"""
        page = parse_page("entities/test.md", raw)
        assert page.frontmatter.title == "Test Page"
        assert page.frontmatter.type == PageType.ENTITY
        assert "ml" in page.frontmatter.tags
        assert "Link" in page.wikilinks

    def test_parse_without_frontmatter(self) -> None:
        raw = "# Simple Page\n\nJust content."
        page = parse_page("simple.md", raw)
        assert page.frontmatter.title == "Simple"
        assert page.frontmatter.type == PageType.CONCEPT
        assert page.content == raw

    def test_multiple_wikilinks(self) -> None:
        raw = "See [[Page A]] and [[Page B]] for more."
        page = parse_page("test.md", raw)
        assert len(page.wikilinks) == 2
        assert "Page A" in page.wikilinks
        assert "Page B" in page.wikilinks


class TestExtractWikilinks:
    """Tests for wikilink extraction."""

    def test_no_links(self) -> None:
        assert extract_wikilinks("No links here.") == []

    def test_single_link(self) -> None:
        assert extract_wikilinks("See [[Target]] for info.") == ["Target"]

    def test_nested_brackets_not_confused(self) -> None:
        assert extract_wikilinks("[normal link](http://x.com)") == []


class TestCreatePageContent:
    """Tests for create_page_content function."""

    def test_basic_page(self) -> None:
        content = create_page_content(
            title="My Page",
            page_type=PageType.CONCEPT,
            content="# My Page\n\nDetails here.",
            tags=["test"],
        )
        assert "---" in content
        assert "title: My Page" in content
        assert "type: concept" in content
        assert "tags:" in content
        assert "- test" in content
        assert "# My Page" in content


class TestContentPreview:
    """Tests for get_content_preview function."""

    def test_short_content(self) -> None:
        text = "Short text."
        assert get_content_preview(text) == "Short text."

    def test_removes_markdown(self) -> None:
        text = "# Heading\n\nSome `code` and **bold** text."
        preview = get_content_preview(text)
        assert "#" not in preview
        assert "`" not in preview
        assert "**" not in preview
        assert "Heading" in preview
