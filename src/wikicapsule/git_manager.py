"""Git wrapper for programmatic wiki operations with safety controls."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import git
from git import Repo

logger = logging.getLogger(__name__)


class GitManagerError(Exception):
    """Base exception for git manager errors."""


class LockError(GitManagerError):
    """Could not acquire or release lock."""


class DirtyWorkingTreeError(GitManagerError):
    """Working tree has uncommitted changes."""


class GitManager:
    """Manages git operations for the wiki directory with file locking."""

    def __init__(self, wiki_dir: Path, lock_timeout: int = 30, auto_commit: bool = True) -> None:
        self.wiki_dir = wiki_dir.expanduser().resolve()
        self.lock_file = self.wiki_dir / ".wikicapsule" / "lock.json"
        self.lock_timeout = lock_timeout
        self.auto_commit = auto_commit
        self._repo: Repo | None = None
        self._has_lock = False

    @property
    def repo(self) -> Repo:
        """Lazy-loaded git repository."""
        if self._repo is None:
            git_dir = self.wiki_dir / ".git"
            if git_dir.exists():
                self._repo = Repo(str(self.wiki_dir))
            else:
                logger.info("Initializing git repository at %s", self.wiki_dir)
                self._repo = Repo.init(str(self.wiki_dir))
                # Create initial commit so we have a HEAD
                readme = self.wiki_dir / "WIKI.md"
                if readme.exists():
                    self._repo.index.add([str(readme)])
                    self._repo.index.commit("[wikicapsule] init: Create wiki schema")
        return self._repo

    def is_dirty(self) -> bool:
        """Check if working tree has uncommitted changes."""
        try:
            return self.repo.is_dirty(untracked_files=True)
        except Exception:
            return False

    def acquire_lock(self) -> bool:
        """Try to acquire the file lock. Returns True if acquired."""
        if self._has_lock:
            return True

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if lock exists and is stale
        if self.lock_file.exists():
            try:
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    lock_data = json.load(f)
                lock_time = lock_data.get("timestamp", 0)
                lock_pid = lock_data.get("pid", 0)

                # Check if owning process is still alive
                if lock_pid > 0:
                    try:
                        os.kill(lock_pid, 0)
                        process_alive = True
                    except OSError:
                        process_alive = False

                    if process_alive and (time.time() - lock_time) < self.lock_timeout:
                        logger.warning("Lock held by PID %d since %.1fs ago", lock_pid, time.time() - lock_time)
                        return False

                logger.info("Removing stale lock from PID %d", lock_pid)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Corrupt lock file, removing: %s", e)

            try:
                self.lock_file.unlink()
            except OSError:
                pass

        # Write our lock
        try:
            lock_data = {"pid": os.getpid(), "timestamp": time.time()}
            with open(self.lock_file, "w", encoding="utf-8") as f:
                json.dump(lock_data, f)
            self._has_lock = True
            logger.debug("Lock acquired by PID %d", os.getpid())
            return True
        except OSError as e:
            logger.error("Failed to write lock file: %s", e)
            return False

    def release_lock(self) -> None:
        """Release the file lock if we hold it."""
        if not self._has_lock:
            return

        try:
            if self.lock_file.exists():
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    lock_data = json.load(f)
                if lock_data.get("pid") == os.getpid():
                    self.lock_file.unlink()
                    logger.debug("Lock released by PID %d", os.getpid())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Error releasing lock: %s", e)
        finally:
            self._has_lock = False

    def ensure_clean(self) -> None:
        """Raise if working tree is dirty (unless we caused it)."""
        if self.is_dirty() and not self._has_lock:
            raise DirtyWorkingTreeError(
                "Working tree has uncommitted changes. "
                "Commit or stash them before proceeding, or run wiki_lint."
            )

    def commit(self, operation: str, summary: str, files: list[Path] | None = None) -> str | None:
        """Commit changes to git. Returns commit hash or None if skipped."""
        if not self.auto_commit:
            logger.debug("Auto-commit disabled, skipping")
            return None

        try:
            if files:
                relative_files = [str(f.relative_to(self.wiki_dir)) for f in files]
                self.repo.index.add(relative_files)
            else:
                self.repo.index.add(".")

            if not self.repo.is_dirty(untracked_files=False):
                logger.debug("No changes to commit")
                return None

            message = f"[wikicapsule] {operation}: {summary}"
            commit_obj = self.repo.index.commit(message)
            commit_hash = commit_obj.hexsha[:8]
            logger.info("Git commit %s: %s", commit_hash, message)
            return commit_hash
        except Exception as e:
            logger.error("Git commit failed: %s", e)
            return None

    def get_status(self) -> dict:
        """Get repository status summary."""
        return {
            "is_dirty": self.is_dirty(),
            "commit_count": len(list(self.repo.iter_commits())),
            "last_commit": self.repo.head.commit.hexsha[:8] if self.repo.head.is_valid() else None,
            "last_commit_message": self.repo.head.commit.message.strip() if self.repo.head.is_valid() else None,
            "untracked_files": self.repo.untracked_files,
            "modified_files": [item.a_path for item in self.repo.index.diff(None)],
            "branch": self.repo.active_branch.name if self.repo.head.is_valid() else "main",
        }

    def __enter__(self) -> "GitManager":
        if not self.acquire_lock():
            raise LockError(f"Could not acquire lock within {self.lock_timeout}s")
        self.ensure_clean()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release_lock()
