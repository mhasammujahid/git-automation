from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime

from zoneinfo import ZoneInfo

from .config import AppConfig
from .file_simulator import FileChangeSimulator
from .git_ops import GitService
from .messages import MessageGenerator
from .scheduler import SchedulingEngine

log = logging.getLogger(__name__)


@dataclass
class RunStats:
    commits_planned: int = 0
    commits_created: int = 0


class ActivityEngine:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.rng = random.Random(cfg.deterministic_seed)
        self.scheduler = SchedulingEngine(cfg, self.rng)
        self.messages = MessageGenerator(cfg, self.rng)
        self.files = FileChangeSimulator(cfg, self.rng)
        self.git = GitService(cfg, self.rng)
        self.tz = ZoneInfo(cfg.timezone)

    def simulate_day(self, when: datetime | None = None) -> RunStats:
        when = when or datetime.now(self.tz)
        today = when.date()
        count = self.scheduler.planned_commits_for_day(today)
        windows = self.scheduler.build_windows(today, count)
        stats = RunStats(commits_planned=count)

        log.info("Planned %s commit(s) for %s", count, today.isoformat())
        for slot in windows:
            work_branch = self.git.maybe_create_work_branch()
            changed = self.files.mutate()
            message = self.messages.generate()
            self.git.commit_all(message=message, commit_time=slot.when)
            self.git.maybe_merge_to_default(work_branch)
            stats.commits_created += 1
            log.info("Committed %s at %s", changed, slot.when.isoformat())

        self.git.push()
        return stats
