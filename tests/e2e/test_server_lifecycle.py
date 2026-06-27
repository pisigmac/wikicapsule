"""End-to-end tests for server lifecycle and MCP protocol."""

from __future__ import annotations

from pathlib import Path

import pytest

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.server import create_mcp_server
from wikicapsule.wiki import WikiManager


@pytest.fixture
def e2e_wiki(tmp_path: Path) -> tuple[WikiManager, WikiCapsuleConfig]:
    """Create a wiki populated with test data."""
    config = WikiCapsuleConfig(wiki_dir=tmp_path)
    wiki = WikiManager(config)

    # Populate with diverse test data
    wiki.create_page(
        path="entities/karpathy.md",
        content="""# Andrej Karpathy

Andrej Karpathy is a computer scientist and deep learning researcher.

## Background

- Former Director of AI at Tesla
- Co-founder of OpenAI
- YouTube educator

## Key Contributions

- [[Neural Networks]] education
- [[Computer Vision]] at Tesla
- [[Large Language Models]] research
""",
        tags=["person", "ai", "deep-learning"],
    )

    wiki.create_page(
        path="concepts/neural-networks.md",
        content="""# Neural Networks

Neural networks are computing systems inspired by biological neural networks.

## Types

- Feedforward networks
- Convolutional networks (CNN)
- Recurrent networks (RNN)
- [[Transformer Architecture]]
""",
        tags=["deep-learning", "fundamentals"],
    )

    wiki.create_page(
        path="concepts/transformer-architecture.md",
        content="""# Transformer Architecture

The Transformer is a deep learning architecture introduced in "Attention Is All You Need".

## Key Innovation

Self-attention mechanism that processes sequences in parallel.

## Components

- Multi-head attention
- Position-wise feed-forward networks
- Layer normalization
""",
        tags=["deep-learning", "nlp", "architecture"],
    )

    wiki.ingest_source(
        source_path="attention-paper.md",
        source_type="paper",
        content="""# Attention Is All You Need

**Authors**: Vaswani et al., 2017

## Abstract

We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.
""",
        tags=["nlp", "transformers"],
    )

    wiki.sync_index()
    return wiki, config


class TestServerCreation:
    """Tests for MCP server creation."""

    def test_server_creation(self, e2e_wiki) -> None:
        wiki, config = e2e_wiki
        mcp = create_mcp_server(config)
        assert mcp.name == "wikicapsule"


class TestPerformanceBudget:
    """Tests for performance requirements."""

    def test_search_latency(self, e2e_wiki) -> None:
        """Search should complete within 500ms."""
        import time

        wiki, config = e2e_wiki

        start = time.time()
        results = wiki.search.search("neural networks", limit=5)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Search took {elapsed:.3f}s, budget is 500ms"
        assert len(results) > 0

    def test_query_latency(self, e2e_wiki) -> None:
        """Query should complete within 2s."""
        import time

        wiki, config = e2e_wiki

        start = time.time()
        result = wiki.query("What are neural networks?")
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Query took {elapsed:.3f}s, budget is 2s"
        assert "Neural Networks" in result or "neural" in result.lower()
