"""Unit tests for git manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from wikicapsule.git_manager import GitManager


class TestGitManager:
    """Tests for GitManager."""

    def test_init_creates_repo(self, tmp_path: Path) -> None:
        gm = GitManager(wiki_dir=tmp_path)
        assert (tmp_path / ".git").exists()

    def test_lock_acquire_release(self, tmp_path: Path) -> None:
        gm = GitManager(wiki_dir=tmp_path, lock_timeout=5)
        assert gm.acquire_lock() is True
        assert gm._has_lock is True
        gm.release_lock()
        assert gm._has_lock is False

    def test_lock_prevents_double_acquire(self, tmp_path: Path) -> None:
        gm1 = GitManager(wiki_dir=tmp_path, lock_timeout=5)
        gm2 = GitManager(wiki_dir=tmp_path, lock_timeout=1)

        assert gm1.acquire_lock() is True
        assert gm2.acquire_lock() is False  # gm1 holds it

        gm1.release_lock()

    def test_context_manager(self, tmp_path: Path) -> None:
        gm = GitManager(wiki_dir=tmp_path, lock_timeout=5)
        with gm as g:
            assert g._has_lock is True
        assert gm._has_lock is False

    def test_commit(self, tmp_path: Path) -> None:
        gm = GitManager(wiki_dir=tmp_path, auto_commit=True)
        # Need to create a file to commit
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        result = gm.commit("test", "test commit", files=[test_file])
        assert result is not None  # Returns commit hash

    def test_get_status(self, tmp_path: Path) -> None:
        gm = GitManager(wiki_dir=tmp_path)
        status = gm.get_status()
        assert "commit_count" in status
        assert "is_dirty" in status
        assert "branch" in status


class TestDirtyTree:
    """Tests for dirty working tree detection."""

    def test_dirty_after_file_change(self, tmp_path: Path) -> None:
        gm = GitManager(wiki_dir=tmp_path, auto_commit=False)
        test_file = tmp_path / "dirty.txt"
        test_file.write_text("changed")

        assert gm.is_dirty() is True
