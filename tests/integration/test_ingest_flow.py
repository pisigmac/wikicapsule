"""Integration tests for the full ingest workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.git_manager import GitManager
from wikicapsule.wiki import WikiManager


@pytest.fixture
def fresh_wiki(tmp_path: Path) -> tuple[WikiManager, WikiCapsuleConfig]:
    """Create a fresh wiki for testing."""
    config = WikiCapsuleConfig(wiki_dir=tmp_path)
    wiki = WikiManager(config)
    return wiki, config


class TestIngestFlow:
    """Tests for full ingest workflow."""

    def test_ingest_article(self, fresh_wiki) -> None:
        wiki, config = fresh_wiki

        result = wiki.ingest_source(
            source_path="test.md",
            source_type="article",
            content="# Test Article\n\nThis is a test article about machine learning.",
            tags=["ml", "test"],
        )

        assert "source_id" in result
        assert result["title"] == "Test Article"

        # Verify wiki page was created
        page = wiki.get_page(result["wiki_path"])
        assert page is not None
        assert "machine learning" in page.content

        # Verify raw was stored
        raw = wiki.get_raw(result["raw_path"])
        assert raw is not None
        assert "Test Article" in raw

    def test_ingest_creates_git_commit(self, fresh_wiki) -> None:
        wiki, config = fresh_wiki

        with GitManager(wiki_dir=config.wiki_dir, auto_commit=True) as git:
            result = wiki.ingest_source(
                source_path="paper.md",
                source_type="paper",
                content="# Research Paper\n\nAbstract here.",
            )

            # Create a test file and commit
            test_file = config.wiki_path / result["wiki_path"]
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# Research Paper\n\nContent")

            commit_hash = git.commit("ingest", f"Ingested paper: {result['title']}")
            assert commit_hash is not None

    def test_index_updated_after_ingest(self, fresh_wiki) -> None:
        wiki, config = fresh_wiki

        wiki.ingest_source(
            source_path="article.md",
            source_type="article",
            content="# Article\n\nContent",
        )

        wiki.sync_index()
        index = wiki.get_page("index.md")
        assert index is not None
        assert "Article" in index.raw_content or "Sources" in index.raw_content


class TestSearchIntegration:
    """Tests for search functionality."""

    def test_search_after_ingest(self, fresh_wiki) -> None:
        wiki, config = fresh_wiki

        wiki.ingest_source(
            source_path="ml.md",
            source_type="article",
            content="# Machine Learning\n\nMachine learning is a subset of artificial intelligence.",
            tags=["ml", "ai"],
        )

        # Also create a concept page
        wiki.create_page(
            path="concepts/machine-learning.md",
            content="# Machine Learning\n\nA field of study that gives computers the ability to learn without being explicitly programmed.",
            tags=["ml"],
        )

        results = wiki.search.search("machine learning", limit=5)
        assert len(results) > 0
        assert any("machine" in r.title.lower() for r in results)

    def test_hybrid_search(self, fresh_wiki) -> None:
        wiki, config = fresh_wiki

        wiki.create_page(
            path="concepts/neural-network.md",
            content="# Neural Network\n\nNeural networks are computing systems inspired by biological neural networks.",
            tags=["deep-learning"],
        )

        results = wiki.search.search_hybrid("neural networks", limit=5)
        assert len(results) >= 1
