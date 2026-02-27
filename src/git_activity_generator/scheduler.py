from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from zoneinfo import ZoneInfo

from .config import AppConfig


@dataclass
class CommitWindow:
    when: datetime


class SchedulingEngine:
    def __init__(self, cfg: AppConfig, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.tz = ZoneInfo(cfg.timezone)

    def is_vacation_day(self, target: date) -> bool:
        for item in self.cfg.vacation_ranges:
            start = datetime.fromisoformat(item["start"]).date()
            end = datetime.fromisoformat(item["end"]).date()
            if start <= target <= end:
                return True
        return False

    def _sample_count(self) -> int:
        if self.cfg.gaussian_distribution:
            mean = (self.cfg.daily_min_commits + self.cfg.daily_max_commits) / 2
            sigma = max((self.cfg.daily_max_commits - self.cfg.daily_min_commits) / 4, 1)
            count = int(round(self.rng.gauss(mean, sigma)))
        else:
            count = self.rng.randint(self.cfg.daily_min_commits, self.cfg.daily_max_commits)
        return min(max(count, self.cfg.daily_min_commits), self.cfg.max_commits_per_day)

    def planned_commits_for_day(self, target: date) -> int:
        if self.is_vacation_day(target):
            return 0

        if self.rng.random() < self.cfg.realism.cooldown_day_probability:
            return 0

        commits = self._sample_count()
        weekday = target.weekday()

        if weekday >= 5:
            commits = int(round(commits * self.cfg.weekend_multiplier))

        month_factor = self.cfg.seasonal.monthly_multiplier.get(target.month, 1.0)
        commits = int(round(commits * month_factor))

        if weekday == 4 and self.rng.random() < self.cfg.realism.pre_weekend_spike_probability:
            commits += self.rng.randint(1, 2)
        if self.rng.random() < self.cfg.realism.streak_burst_probability:
            commits += self.rng.randint(1, 3)

        return max(0, min(commits, self.cfg.max_commits_per_day))

    def build_windows(self, target: date, count: int) -> list[CommitWindow]:
        windows: list[CommitWindow] = []
        for _ in range(count):
            hour = self.rng.randint(self.cfg.working_hours_start, self.cfg.working_hours_end)
            if self.rng.random() < self.cfg.realism.late_night_probability:
                hour = self.rng.choice([22, 23, 0, 1])
            minute = self.rng.randint(0, 59)
            second = self.rng.randint(0, 59)
            dt = datetime(target.year, target.month, target.day, hour, minute, second)
            windows.append(CommitWindow(when=dt.replace(tzinfo=self.tz)))

        windows.sort(key=lambda x: x.when)

        # small jitter to avoid exact spacing
        for idx in range(1, len(windows)):
            if windows[idx].when <= windows[idx - 1].when:
                windows[idx].when = windows[idx - 1].when + timedelta(minutes=1)

        return windows

