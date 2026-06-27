"""Configuration loading, validation, and defaults for WikiCapsule."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """Server runtime configuration."""

    transport: str = Field(default="stdio", description="stdio or sse")
    port: int = Field(default=8080, description="Port for SSE mode")
    log_level: str = Field(default="INFO")

    @field_validator("transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        if v not in {"stdio", "sse"}:
            raise ValueError("transport must be 'stdio' or 'sse'")
        return v


class SearchConfig(BaseModel):
    """Search engine configuration."""

    vector_model: str = Field(default="all-MiniLM-L6-v2")
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    rebuild_threshold: int = Field(default=10, ge=1)


class WikiConfig(BaseModel):
    """Wiki behavior configuration."""

    auto_commit: bool = Field(default=True)
    commit_message_template: str = Field(default="[wikicapsule] {operation}: {summary}")
    lock_timeout_seconds: int = Field(default=30, ge=5)
    search: SearchConfig = Field(default_factory=SearchConfig)


class IngestConfig(BaseModel):
    """Ingest workflow configuration."""

    default_tags: list[str] = Field(default_factory=list)
    extract_images: bool = Field(default=True)
    summary_max_length: int = Field(default=2000, ge=100)


class LintConfig(BaseModel):
    """Lint workflow configuration."""

    orphan_threshold_days: int = Field(default=30, ge=1)
    stale_check_enabled: bool = Field(default=True)


class WikiCapsuleConfig(BaseSettings):
    """Root configuration for WikiCapsule."""

    model_config = SettingsConfigDict(
        env_prefix="WIKICAPSULE_",
        env_nested_delimiter="__",
        yaml_file=".wikicapsule/config.yaml",
        extra="ignore",
    )

    wiki_dir: Path = Field(default=Path("."), description="Root wiki directory")
    transport: str = Field(default="stdio")
    port: int = Field(default=8080)
    log_level: str = Field(default="INFO")

    server: ServerConfig = Field(default_factory=ServerConfig)
    wiki: WikiConfig = Field(default_factory=WikiConfig)
    ingest: IngestConfig = Field(default_factory=IngestConfig)
    lint: LintConfig = Field(default_factory=LintConfig)

    @field_validator("wiki_dir")
    @classmethod
    def resolve_wiki_dir(cls, v: Path) -> Path:
        return v.expanduser().resolve()

    @property
    def wiki_path(self) -> Path:
        """Path to wiki/ directory."""
        return self.wiki_dir / "wiki"

    @property
    def raw_path(self) -> Path:
        """Path to raw/ directory."""
        return self.wiki_dir / "raw"

    @property
    def dot_wikicapsule_path(self) -> Path:
        """Path to .wikicapsule/ directory."""
        return self.wiki_dir / ".wikicapsule"

    @property
    def search_db_path(self) -> Path:
        """Path to SQLite search database."""
        return self.dot_wikicapsule_path / "search.db"

    @property
    def lock_file_path(self) -> Path:
        """Path to lock file."""
        return self.dot_wikicapsule_path / "lock.json"

    @property
    def config_file_path(self) -> Path:
        """Path to config YAML file."""
        return self.dot_wikicapsule_path / "config.yaml"

    @property
    def wiki_md_path(self) -> Path:
        """Path to WIKI.md schema document."""
        return self.wiki_dir / "WIKI.md"

    @classmethod
    def from_yaml(cls, path: Path | str | None = None) -> "WikiCapsuleConfig":
        """Load configuration from YAML file, falling back to defaults."""
        if path is None:
            wiki_dir = Path(os.environ.get("WIKICAPSULE_WIKI_DIR", ".")).expanduser().resolve()
            path = wiki_dir / ".wikicapsule" / "config.yaml"
        else:
            path = Path(path).expanduser().resolve()

        kwargs: dict[str, Any] = {}

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Map nested YAML to our structure
            if "server" in data:
                kwargs["server"] = ServerConfig(**data["server"])
            if "wiki" in data:
                wiki_data = data["wiki"].copy()
                if "search" in wiki_data:
                    wiki_data["search"] = SearchConfig(**wiki_data["search"])
                kwargs["wiki"] = WikiConfig(**wiki_data)
            if "ingest" in data:
                kwargs["ingest"] = IngestConfig(**data["ingest"])
            if "lint" in data:
                kwargs["lint"] = LintConfig(**data["lint"])

        # Environment overrides
        if wiki_dir_env := os.environ.get("WIKICAPSULE_WIKI_DIR"):
            kwargs["wiki_dir"] = Path(wiki_dir_env).expanduser().resolve()
        if transport_env := os.environ.get("WIKICAPSULE_TRANSPORT"):
            kwargs["transport"] = transport_env
        if port_env := os.environ.get("WIKICAPSULE_PORT"):
            kwargs["port"] = int(port_env)
        if log_level_env := os.environ.get("WIKICAPSULE_LOG_LEVEL"):
            kwargs["log_level"] = log_level_env

        return cls(**kwargs)

    def to_yaml(self) -> str:
        """Serialize configuration to YAML string."""
        data = {
            "server": {
                "transport": self.server.transport,
                "port": self.server.port,
                "log_level": self.server.log_level,
            },
            "wiki": {
                "auto_commit": self.wiki.auto_commit,
                "commit_message_template": self.wiki.commit_message_template,
                "lock_timeout_seconds": self.wiki.lock_timeout_seconds,
                "search": {
                    "vector_model": self.wiki.search.vector_model,
                    "hybrid_alpha": self.wiki.search.hybrid_alpha,
                    "rebuild_threshold": self.wiki.search.rebuild_threshold,
                },
            },
            "ingest": {
                "default_tags": self.ingest.default_tags,
                "extract_images": self.ingest.extract_images,
                "summary_max_length": self.ingest.summary_max_length,
            },
            "lint": {
                "orphan_threshold_days": self.lint.orphan_threshold_days,
                "stale_check_enabled": self.lint.stale_check_enabled,
            },
        }
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def save(self, path: Path | str | None = None) -> None:
        """Save configuration to YAML file."""
        if path is None:
            path = self.config_file_path
        else:
            path = Path(path).expanduser().resolve()

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_yaml())
