from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SeasonalProfile:
    monthly_multiplier: dict[int, float] = field(default_factory=dict)


@dataclass
class BranchingConfig:
    enabled: bool = True
    feature_branch_probability: float = 0.25
    hotfix_branch_probability: float = 0.05
    squash_merge_probability: float = 0.4


@dataclass
class MessageConfig:
    conventional_commits: bool = True
    emoji: bool = False
    tone: str = "startup"
    typo_probability: float = 0.06
    markov_enabled: bool = True
    ai_templates_enabled: bool = True


@dataclass
class RealismConfig:
    streak_burst_probability: float = 0.15
    late_night_probability: float = 0.12
    pre_weekend_spike_probability: float = 0.2
    large_refactor_probability: float = 0.08
    cooldown_day_probability: float = 0.05


@dataclass
class AuthorProfile:
    name: str
    email: str


@dataclass
class AppConfig:
    repo_path: str
    default_branch: str = "main"
    timezone: str = "UTC"
    daily_min_commits: int = 1
    daily_max_commits: int = 8
    max_commits_per_day: int = 12
    gaussian_distribution: bool = True
    weekend_multiplier: float = 0.45
    working_hours_start: int = 9
    working_hours_end: int = 19
    dry_run: bool = False
    verbose: bool = True
    deterministic_seed: int | None = None
    vacation_ranges: list[dict[str, str]] = field(default_factory=list)
    seasonal: SeasonalProfile = field(default_factory=SeasonalProfile)
    branching: BranchingConfig = field(default_factory=BranchingConfig)
    messages: MessageConfig = field(default_factory=MessageConfig)
    realism: RealismConfig = field(default_factory=RealismConfig)
    authors: list[AuthorProfile] = field(default_factory=list)


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _load_raw(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)

    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "YAML config requires PyYAML. Install dependencies or use JSON config."
        ) from exc


def load_config(config_path: str | Path) -> AppConfig:
    config_path = Path(config_path)
    raw = _load_raw(config_path)

    env_override: dict[str, Any] = {}
    if os.getenv("GAG_REPO_PATH"):
        env_override["repo_path"] = os.getenv("GAG_REPO_PATH")
    if os.getenv("GAG_DRY_RUN"):
        env_override["dry_run"] = os.getenv("GAG_DRY_RUN", "false").lower() == "true"

    raw = _merge_dict(raw, env_override)
    authors = [AuthorProfile(**author) for author in raw.get("authors", [])]

    return AppConfig(
        repo_path=raw["repo_path"],
        default_branch=raw.get("default_branch", "main"),
        timezone=raw.get("timezone", "UTC"),
        daily_min_commits=raw.get("daily_min_commits", 1),
        daily_max_commits=raw.get("daily_max_commits", 8),
        max_commits_per_day=raw.get("max_commits_per_day", 12),
        gaussian_distribution=raw.get("gaussian_distribution", True),
        weekend_multiplier=raw.get("weekend_multiplier", 0.45),
        working_hours_start=raw.get("working_hours_start", 9),
        working_hours_end=raw.get("working_hours_end", 19),
        dry_run=raw.get("dry_run", False),
        verbose=raw.get("verbose", True),
        deterministic_seed=raw.get("deterministic_seed"),
        vacation_ranges=raw.get("vacation_ranges", []),
        seasonal=SeasonalProfile(monthly_multiplier={int(k): v for k, v in raw.get("seasonal", {}).get("monthly_multiplier", {}).items()}),
        branching=BranchingConfig(**raw.get("branching", {})),
        messages=MessageConfig(**raw.get("messages", {})),
        realism=RealismConfig(**raw.get("realism", {})),
        authors=authors,
    )
