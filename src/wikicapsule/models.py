"""Pydantic models for WikiCapsule data structures."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PageType(str, Enum):
    """Types of wiki pages."""

    ENTITY = "entity"
    CONCEPT = "concept"
    SOURCE = "source"
    COMPARISON = "comparison"
    EXPLORATION = "exploration"
    INDEX = "index"
    LOG = "log"
    OVERVIEW = "overview"


class PageStatus(str, Enum):
    """Status of a wiki page."""

    DRAFT = "draft"
    REVIEW = "review"
    STABLE = "stable"


class Frontmatter(BaseModel):
    """YAML frontmatter schema for wiki pages."""

    title: str = Field(..., description="Human-readable page title")
    type: PageType = Field(default=PageType.CONCEPT, description="Page category")
    tags: list[str] = Field(default_factory=list, description="Topic tags")
    sources: list[str] = Field(default_factory=list, description="Source IDs this page references")
    created: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    status: PageStatus = Field(default=PageStatus.DRAFT, description="Content maturity")

    model_config = {"populate_by_name": True}


class WikiPage(BaseModel):
    """A wiki page with parsed frontmatter and content."""

    path: str = Field(..., description="Relative path in wiki/ directory")
    frontmatter: Frontmatter
    content: str = Field(..., description="Markdown body (excluding frontmatter)")
    raw_content: str = Field(..., description="Full markdown with frontmatter")
    wikilinks: list[str] = Field(default_factory=list, description="[[Page Name]] references")


class SourceDocument(BaseModel):
    """A raw source document that has been ingested."""

    id: str = Field(..., description="UUID or slug identifier")
    path: str = Field(..., description="Path in raw/ directory")
    title: str = Field(..., description="Document title")
    type: str = Field(..., description="article/paper/book_chapter/transcript/note")
    tags: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """Request to ingest a source document."""

    source_path: str = Field(..., description="Path to the source file or URL")
    source_type: str = Field(..., description="Type of source")
    tags: list[str] = Field(default_factory=list)
    content: str | None = Field(default=None, description="Optional inline content")

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        allowed = {"article", "paper", "book_chapter", "transcript", "note"}
        if v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v


class QueryRequest(BaseModel):
    """Request to query the wiki."""

    question: str = Field(..., min_length=1, description="Natural language question")
    output_format: str = Field(default="markdown", description="markdown/table/slides/chart")

    @field_validator("output_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed = {"markdown", "table", "slides", "chart"}
        if v not in allowed:
            raise ValueError(f"output_format must be one of {allowed}")
        return v


class SearchRequest(BaseModel):
    """Request to search wiki pages."""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    search_type: str = Field(default="hybrid", alias="type")

    @field_validator("search_type")
    @classmethod
    def validate_search_type(cls, v: str) -> str:
        allowed = {"bm25", "vector", "hybrid"}
        if v not in allowed:
            raise ValueError(f"search_type must be one of {allowed}")
        return v


class LintRequest(BaseModel):
    """Request to lint the wiki."""

    scope: str = Field(default="quick")
    auto_fix: bool = Field(default=False)

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        allowed = {"full", "quick"}
        if v not in allowed:
            raise ValueError(f"scope must be one of {allowed}")
        return v


class PageCreateRequest(BaseModel):
    """Request to create a new wiki page."""

    path: str = Field(..., pattern=r"^[a-z0-9][a-z0-9_\-\/]*\.md$")
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class PageUpdateRequest(BaseModel):
    """Request to update an existing wiki page."""

    path: str = Field(...)
    content: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class SearchResult(BaseModel):
    """A single search result."""

    path: str = Field(..., description="Wiki page path")
    title: str = Field(..., description="Page title")
    score: float = Field(..., description="Relevance score (higher = better)")
    snippet: str = Field(default="", description="Text excerpt around match")
    search_type: str = Field(default="bm25", description="Which search produced this result")


class LintIssue(BaseModel):
    """A single lint issue found in the wiki."""

    severity: str = Field(..., description="error/warning/info")
    category: str = Field(..., description="orphan/stale/contradiction/missing/broken-link")
    message: str = Field(...)
    page_path: str | None = Field(default=None)
    suggestion: str | None = Field(default=None)


class WikiStats(BaseModel):
    """Statistics about the wiki."""

    total_pages: int = Field(default=0)
    total_sources: int = Field(default=0)
    total_entities: int = Field(default=0)
    total_concepts: int = Field(default=0)
    total_comparisons: int = Field(default=0)
    total_explorations: int = Field(default=0)
    pages_by_status: dict[str, int] = Field(default_factory=dict)
    pages_by_tag: dict[str, int] = Field(default_factory=dict)
    last_ingest: datetime | None = Field(default=None)
    last_update: datetime | None = Field(default=None)
    git_commits: int = Field(default=0)
    index_size_mb: float = Field(default=0.0)


class LogEntry(BaseModel):
    """A single log entry."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operation: str = Field(..., description="ingest/query/lint/search/create/update")
    summary: str = Field(...)
    details: dict[str, Any] = Field(default_factory=dict)
