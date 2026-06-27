"""Unit tests for WikiCapsule models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wikicapsule.models import (
    Frontmatter,
    IngestRequest,
    LintRequest,
    PageCreateRequest,
    PageStatus,
    PageType,
    PageUpdateRequest,
    QueryRequest,
    SearchRequest,
    WikiPage,
    WikiStats,
)


class TestFrontmatter:
    """Tests for Frontmatter model."""

    def test_default_frontmatter(self) -> None:
        fm = Frontmatter(title="Test Page")
        assert fm.title == "Test Page"
        assert fm.type == PageType.CONCEPT
        assert fm.tags == []
        assert fm.status == PageStatus.DRAFT

    def test_frontmatter_with_tags(self) -> None:
        fm = Frontmatter(title="Test", tags=["ml", "ai"], status=PageStatus.STABLE)
        assert fm.tags == ["ml", "ai"]
        assert fm.status == PageStatus.STABLE

    def test_invalid_status(self) -> None:
        with pytest.raises(ValidationError):
            Frontmatter(title="Test", status="invalid_status")


class TestIngestRequest:
    """Tests for IngestRequest model."""

    def test_valid_ingest(self) -> None:
        req = IngestRequest(source_path="./article.md", source_type="article")
        assert req.source_type == "article"

    def test_invalid_source_type(self) -> None:
        with pytest.raises(ValidationError):
            IngestRequest(source_path="./x.md", source_type="invalid")

    def test_valid_source_types(self) -> None:
        for st in ["article", "paper", "book_chapter", "transcript", "note"]:
            req = IngestRequest(source_path="./x.md", source_type=st)
            assert req.source_type == st


class TestQueryRequest:
    """Tests for QueryRequest model."""

    def test_valid_query(self) -> None:
        req = QueryRequest(question="What is ML?")
        assert req.output_format == "markdown"

    def test_invalid_format(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="What?", output_format="invalid")

    def test_empty_question(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="")


class TestSearchRequest:
    """Tests for SearchRequest model."""

    def test_default_hybrid(self) -> None:
        req = SearchRequest(query="test")
        assert req.search_type == "hybrid"

    def test_valid_types(self) -> None:
        for t in ["bm25", "vector", "hybrid"]:
            req = SearchRequest(query="test", type=t)
            assert req.search_type == t


class TestPageCreateRequest:
    """Tests for PageCreateRequest model."""

    def test_valid_path(self) -> None:
        req = PageCreateRequest(path="entities/test-page.md", content="# Test")
        assert req.path == "entities/test-page.md"

    def test_invalid_path(self) -> None:
        with pytest.raises(ValidationError):
            PageCreateRequest(path="invalid", content="test")


class TestWikiPage:
    """Tests for WikiPage model."""

    def test_wiki_page_creation(self) -> None:
        fm = Frontmatter(title="Test")
        page = WikiPage(
            path="concepts/test.md",
            frontmatter=fm,
            content="# Test\n\nContent",
            raw_content="---\ntitle: Test\n---\n\n# Test\n\nContent",
            wikilinks=["Other Page"],
        )
        assert page.path == "concepts/test.md"
        assert "Other Page" in page.wikilinks


class TestWikiStats:
    """Tests for WikiStats model."""

    def test_default_stats(self) -> None:
        stats = WikiStats()
        assert stats.total_pages == 0
        assert stats.total_entities == 0
