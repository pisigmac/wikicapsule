"""Hybrid search engine — BM25 (FTS5) + vector search with RRF fusion."""

from __future__ import annotations

import json
import logging
import pickle
import sqlite3
import struct
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from wikicapsule.models import SearchResult

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class SearchEngine:
    """Hybrid search engine combining BM25 and vector search."""

    def __init__(
        self,
        db_path: Path,
        model_name: str = "all-MiniLM-L6-v2",
        hybrid_alpha: float = 0.5,
    ) -> None:
        self.db_path = db_path
        self.model_name = model_name
        self.hybrid_alpha = hybrid_alpha
        self._model: SentenceTransformer | None = None
        self._ensure_schema()

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load sentence transformer model."""
        if self._model is None:
            logger.info("Loading sentence transformer model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _ensure_schema(self) -> None:
        """Create SQLite tables and FTS5 virtual table if not present."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT,
                    tags TEXT,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                    path, title, content,
                    content='pages', content_rowid='id'
                );

                CREATE TABLE IF NOT EXISTS page_embeddings (
                    page_id INTEGER PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operation TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details TEXT
                );

                -- Triggers to keep FTS index in sync
                CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
                    INSERT INTO pages_fts(rowid, path, title, content)
                    VALUES (new.id, new.path, new.title, new.content);
                END;

                CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
                    INSERT INTO pages_fts(pages_fts, rowid, path, title, content)
                    VALUES ('delete', old.id, old.path, old.title, old.content);
                END;

                CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
                    INSERT INTO pages_fts(pages_fts, rowid, path, title, content)
                    VALUES ('delete', old.id, old.path, old.title, old.content);
                    INSERT INTO pages_fts(rowid, path, title, content)
                    VALUES (new.id, new.path, new.title, new.content);
                END;
            """)

    def index_page(
        self,
        path: str,
        title: str,
        content: str,
        page_type: str | None = None,
        tags: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> int:
        """Add or update a page in the search index.

        Returns:
            Page ID in the database
        """
        tags_json = json.dumps(tags or [])
        sources_json = json.dumps(sources or [])

        with sqlite3.connect(str(self.db_path)) as conn:
            # Upsert page
            conn.execute(
                """
                INSERT INTO pages (path, title, content, type, tags, sources, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(path) DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    type=excluded.type,
                    tags=excluded.tags,
                    sources=excluded.sources,
                    updated_at=datetime('now')
                """,
                (path, title, content, page_type, tags_json, sources_json),
            )

            cursor = conn.execute("SELECT id FROM pages WHERE path = ?", (path,))
            page_id = cursor.fetchone()[0]

            # Compute and store embedding
            embedding = self.model.encode(content, show_progress_bar=False)
            embedding_bytes = struct.pack(f"{len(embedding)}f", *embedding.astype(np.float32))

            conn.execute(
                """
                INSERT INTO page_embeddings (page_id, embedding)
                VALUES (?, ?)
                ON CONFLICT(page_id) DO UPDATE SET embedding=excluded.embedding
                """,
                (page_id, embedding_bytes),
            )

        logger.debug("Indexed page '%s' (id=%d)", path, page_id)
        return page_id

    def remove_page(self, path: str) -> None:
        """Remove a page from the search index."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM pages WHERE path = ?", (path,))
        logger.debug("Removed page '%s' from index", path)

    def search_bm25(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search using BM25 over FTS5."""
        # Escape FTS5 special characters
        escaped = query.replace('"', '""')
        fts_query = f'"{escaped}"'

        with sqlite3.connect(str(self.db_path)) as conn:
            # Enable BM25 ranking
            cursor = conn.execute(
                """
                SELECT p.path, p.title, p.content, rank
                FROM pages_fts
                JOIN pages p ON pages_fts.rowid = p.id
                WHERE pages_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit),
            )
            rows = cursor.fetchall()

        results = []
        for path, title, content, rank in rows:
            # rank is negative BM25, so negate for score
            score = -rank if rank else 0.0
            snippet = self._make_snippet(content, query)
            results.append(
                SearchResult(
                    path=path, title=title, score=score, snippet=snippet, search_type="bm25"
                )
            )

        return results

    def search_vector(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search using vector similarity."""
        query_embedding = self.model.encode(query, show_progress_bar=False).astype(np.float32)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                SELECT p.path, p.title, p.content, e.embedding
                FROM page_embeddings e
                JOIN pages p ON e.page_id = p.id
                """
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        # Compute similarities in numpy
        results = []
        for path, title, content, embedding_bytes in rows:
            embedding = np.array(struct.unpack(f"{EMBEDDING_DIM}f", embedding_bytes), dtype=np.float32)
            similarity = self._cosine_similarity(query_embedding, embedding)
            snippet = self._make_snippet(content, query)
            results.append(
                SearchResult(
                    path=path,
                    title=title,
                    score=float(similarity),
                    snippet=snippet,
                    search_type="vector",
                )
            )

        # Sort by similarity descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def search_hybrid(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search using reciprocal rank fusion of BM25 and vector results."""
        bm25_results = self.search_bm25(query, limit=limit * 2)
        vector_results = self.search_vector(query, limit=limit * 2)

        # Build score maps
        bm25_map: dict[str, float] = {}
        for rank, r in enumerate(bm25_results, start=1):
            bm25_map[r.path] = 1.0 / (rank + 60)  # RRF constant k=60

        vector_map: dict[str, float] = {}
        for rank, r in enumerate(vector_results, start=1):
            vector_map[r.path] = 1.0 / (rank + 60)

        # Combine with alpha weighting
        all_paths = set(bm25_map.keys()) | set(vector_map.keys())
        fused: list[tuple[str, float]] = []

        for path in all_paths:
            bm25_score = bm25_map.get(path, 0.0)
            vec_score = vector_map.get(path, 0.0)
            # Weighted RRF
            combined = (1 - self.hybrid_alpha) * bm25_score + self.hybrid_alpha * vec_score
            fused.append((path, combined))

        fused.sort(key=lambda x: x[1], reverse=True)

        # Build final results using best metadata from either source
        title_map = {r.path: r for r in bm25_results + vector_results}

        final_results = []
        for path, score in fused[:limit]:
            ref = title_map.get(path)
            if ref:
                final_results.append(
                    SearchResult(
                        path=path,
                        title=ref.title,
                        score=score,
                        snippet=ref.snippet,
                        search_type="hybrid",
                    )
                )

        return final_results

    def search(self, query: str, limit: int = 10, search_type: str = "hybrid") -> list[SearchResult]:
        """Dispatch to the appropriate search method."""
        start = time.time()

        if search_type == "bm25":
            results = self.search_bm25(query, limit)
        elif search_type == "vector":
            results = self.search_vector(query, limit)
        else:
            results = self.search_hybrid(query, limit)

        elapsed = time.time() - start
        logger.info("Search '%s' (%s) returned %d results in %.3fs", query, search_type, len(results), elapsed)
        return results

    def add_source(self, source_id: str, path: str, title: str, source_type: str) -> None:
        """Record an ingested source."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO sources (id, path, title, type)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    path=excluded.path,
                    title=excluded.title,
                    type=excluded.type
                """,
                (source_id, path, title, source_type),
            )

    def add_log(self, operation: str, summary: str, details: dict | None = None) -> None:
        """Add a log entry."""
        details_json = json.dumps(details) if details else None
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO log (operation, summary, details) VALUES (?, ?, ?)",
                (operation, summary, details_json),
            )

    def get_stats(self) -> dict:
        """Get search index statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            page_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
            source_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            embedding_count = conn.execute("SELECT COUNT(*) FROM page_embeddings").fetchone()[0]
            log_count = conn.execute("SELECT COUNT(*) FROM log").fetchone()[0]
            db_size = self.db_path.stat().st_size / (1024 * 1024)

        return {
            "indexed_pages": page_count,
            "indexed_sources": source_count,
            "embeddings": embedding_count,
            "log_entries": log_count,
            "db_size_mb": round(db_size, 2),
        }

    def clear(self) -> None:
        """Clear all indexed data."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM page_embeddings")
            conn.execute("DELETE FROM pages")
            conn.execute("DELETE FROM sources")
            conn.execute("DELETE FROM log")
        logger.info("Search index cleared")

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _make_snippet(content: str, query: str, max_length: int = 200) -> str:
        """Create a text snippet around query terms."""
        content_lower = content.lower()
        query_lower = query.lower()

        idx = content_lower.find(query_lower)
        if idx == -1:
            # Try finding individual words
            words = query_lower.split()
            for word in words:
                idx = content_lower.find(word)
                if idx != -1:
                    break

        if idx == -1:
            return content[:max_length].strip() + ("..." if len(content) > max_length else "")

        start = max(0, idx - max_length // 2)
        end = min(len(content), idx + max_length // 2)
        snippet = content[start:end].strip()

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(content) else ""
        return prefix + snippet + suffix
