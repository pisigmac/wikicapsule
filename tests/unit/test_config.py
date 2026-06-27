"""Unit tests for configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from wikicapsule.config import WikiCapsuleConfig


class TestConfigDefaults:
    """Tests for default configuration."""

    def test_default_values(self) -> None:
        config = WikiCapsuleConfig()
        assert config.server.transport == "stdio"
        assert config.server.port == 8080
        assert config.server.log_level == "INFO"
        assert config.wiki.auto_commit is True
        assert config.wiki.lock_timeout_seconds == 30
        assert config.wiki.search.vector_model == "all-MiniLM-L6-v2"
        assert config.wiki.search.hybrid_alpha == 0.5

    def test_derived_paths(self, tmp_path: Path) -> None:
        config = WikiCapsuleConfig(wiki_dir=tmp_path)
        assert config.wiki_path == tmp_path / "wiki"
        assert config.raw_path == tmp_path / "raw"
        assert config.dot_wikicapsule_path == tmp_path / ".wikicapsule"
        assert config.search_db_path == tmp_path / ".wikicapsule" / "search.db"
        assert config.lock_file_path == tmp_path / ".wikicapsule" / "lock.json"


class TestConfigFromYaml:
    """Tests for YAML configuration loading."""

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        config_data = {
            "server": {"transport": "sse", "port": 9000, "log_level": "DEBUG"},
            "wiki": {
                "auto_commit": False,
                "lock_timeout_seconds": 60,
                "search": {"vector_model": "custom-model", "hybrid_alpha": 0.7},
            },
            "ingest": {"summary_max_length": 1000},
        }

        config_file = tmp_path / ".wikicapsule" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = WikiCapsuleConfig.from_yaml(config_file)
        assert config.server.transport == "sse"
        assert config.server.port == 9000
        assert config.wiki.auto_commit is False
        assert config.wiki.search.vector_model == "custom-model"
        assert config.wiki.search.hybrid_alpha == 0.7
        assert config.ingest.summary_max_length == 1000

    def test_missing_file_uses_defaults(self, tmp_path: Path) -> None:
        config = WikiCapsuleConfig.from_yaml(tmp_path / "nonexistent.yaml")
        assert config.server.transport == "stdio"


class TestConfigSave:
    """Tests for configuration saving."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        config = WikiCapsuleConfig(
            wiki_dir=tmp_path,
            server_transport="sse",
            server_port=9090,
        )
        config.save()

        assert config.config_file_path.exists()

        loaded = WikiCapsuleConfig.from_yaml(config.config_file_path)
        assert loaded.server.transport == "sse"
        assert loaded.server.port == 9090


class TestConfigSerialization:
    """Tests for config to/from YAML."""

    def test_to_yaml(self) -> None:
        config = WikiCapsuleConfig()
        yaml_str = config.to_yaml()
        assert "server:" in yaml_str
        assert "wiki:" in yaml_str
        assert "all-MiniLM-L6-v2" in yaml_str
