from __future__ import annotations

import logging
import os
import random
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import AppConfig, AuthorProfile

log = logging.getLogger(__name__)


@dataclass
class CommitResult:
    branch: str
    sha: str | None


class GitService:
    def __init__(self, cfg: AppConfig, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.repo = Path(cfg.repo_path)

    def _run(self, *args: str, env: dict[str, str] | None = None) -> str:
        cmd = ["git", *args]
        log.debug("Running: %s", " ".join(cmd))
        out = subprocess.run(cmd, cwd=self.repo, env=env, check=True, text=True, capture_output=True)
        return out.stdout.strip()

    def _current_branch(self) -> str:
        return self._run("rev-parse", "--abbrev-ref", "HEAD")

    def _pick_author(self) -> AuthorProfile | None:
        return self.rng.choice(self.cfg.authors) if self.cfg.authors else None

    def maybe_create_work_branch(self) -> str:
        branch = self._current_branch()
        if not self.cfg.branching.enabled:
            return branch

        roll = self.rng.random()
        if roll < self.cfg.branching.hotfix_branch_probability:
            branch = f"hotfix/auto-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            self._run("checkout", "-b", branch)
        elif roll < self.cfg.branching.hotfix_branch_probability + self.cfg.branching.feature_branch_probability:
            branch = f"feature/auto-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            self._run("checkout", "-b", branch)
        return branch

    def commit_all(self, message: str, commit_time: datetime) -> CommitResult:
        if self.cfg.dry_run:
            log.info("[dry-run] commit: %s @ %s", message, commit_time.isoformat())
            return CommitResult(branch=self._current_branch(), sha=None)

        env = os.environ.copy()
        author = self._pick_author()
        if author:
            env["GIT_AUTHOR_NAME"] = author.name
            env["GIT_AUTHOR_EMAIL"] = author.email
            env["GIT_COMMITTER_NAME"] = author.name
            env["GIT_COMMITTER_EMAIL"] = author.email

        timestamp = commit_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        env["GIT_AUTHOR_DATE"] = timestamp
        env["GIT_COMMITTER_DATE"] = timestamp

        self._run("add", "-A")
        self._run("commit", "-m", message, env=env)
        sha = self._run("rev-parse", "HEAD")
        return CommitResult(branch=self._current_branch(), sha=sha)

    def maybe_merge_to_default(self, work_branch: str) -> None:
        if work_branch == self.cfg.default_branch or not self.cfg.branching.enabled or self.cfg.dry_run:
            return
        self._run("checkout", self.cfg.default_branch)
        if self.rng.random() < self.cfg.branching.squash_merge_probability:
            self._run("merge", "--squash", work_branch)
            self._run("commit", "-m", f"chore(merge): squash merge {work_branch}")
        else:
            self._run("merge", "--no-ff", work_branch, "-m", f"chore(merge): merge {work_branch}")
        self._run("branch", "-D", work_branch)

    def push(self) -> None:
        if self.cfg.dry_run:
            log.info("[dry-run] push skipped")
            return
        self._run("push", "origin", self.cfg.default_branch)
