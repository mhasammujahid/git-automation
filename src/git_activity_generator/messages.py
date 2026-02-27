from __future__ import annotations

import random
import re
from collections import defaultdict

from .config import AppConfig

TYPES = ["feature", "bugfix", "refactor", "docs", "chore", "test", "perf"]
SCOPES = ["auth", "api", "ui", "worker", "db", "core", "scheduler", "cli"]
COMPONENTS = ["session manager", "build pipeline", "cache layer", "config loader", "metrics collector"]
FILES = ["src/app.py", "src/api/routes.py", "README.md", "config/settings.yaml", "tests/test_core.py"]

TONE_TEMPLATES = {
    "startup": [
        "ship {type} for {component}",
        "iterate on {component} behavior",
        "tighten {scope} flow for faster delivery",
    ],
    "enterprise": [
        "align {component} with compliance requirement",
        "stabilize {scope} path under heavy load",
        "improve observability for {component}",
    ],
    "solo dev": [
        "polish {component} before next milestone",
        "cleanup {scope} logic and comments",
        "add notes for {file}",
    ],
}


class MessageGenerator:
    def __init__(self, cfg: AppConfig, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.markov = self._build_markov_chain()

    def _build_markov_chain(self) -> dict[str, list[str]]:
        corpus = [
            "add endpoint validation for token refresh",
            "fix flaky worker queue retry path",
            "refactor scheduler date arithmetic",
            "update docs for branch automation flow",
            "improve test coverage around commit generator",
            "optimize file mutation batching logic",
        ]
        graph: dict[str, list[str]] = defaultdict(list)
        for sentence in corpus:
            words = ["__start__"] + sentence.split() + ["__end__"]
            for i in range(len(words) - 1):
                graph[words[i]].append(words[i + 1])
        return graph

    def _markov_sentence(self, max_words: int = 10) -> str:
        token = "__start__"
        out: list[str] = []
        while len(out) < max_words:
            nxt = self.rng.choice(self.markov[token])
            if nxt == "__end__":
                break
            out.append(nxt)
            token = nxt
        return " ".join(out)

    def _inject_typo(self, text: str) -> str:
        if len(text) < 6:
            return text
        idx = self.rng.randint(1, len(text) - 2)
        return text[:idx] + text[idx + 1] + text[idx] + text[idx + 2 :]

    def generate(self) -> str:
        change_type = self.rng.choice(TYPES)
        scope = self.rng.choice(SCOPES)
        component = self.rng.choice(COMPONENTS)
        file_ref = self.rng.choice(FILES)
        issue = self.rng.randint(10, 999)

        tone = self.cfg.messages.tone if self.cfg.messages.tone in TONE_TEMPLATES else "startup"
        template = self.rng.choice(TONE_TEMPLATES[tone]).format(
            type=change_type,
            component=component,
            scope=scope,
            file=file_ref,
        )

        if self.cfg.messages.markov_enabled and self.rng.random() < 0.35:
            template = self._markov_sentence()

        summary = f"{template} (#{issue}) [{file_ref}]"

        if self.cfg.messages.conventional_commits:
            cc_type = {
                "feature": "feat",
                "bugfix": "fix",
                "refactor": "refactor",
                "docs": "docs",
                "chore": "chore",
                "test": "test",
                "perf": "perf",
            }[change_type]
            summary = f"{cc_type}({scope}): {summary}"

        if self.cfg.messages.emoji:
            summary = self.rng.choice(["✨", "🐛", "🧹", "📝", "⚡"]) + " " + summary

        if self.cfg.messages.typo_probability > 0 and self.rng.random() < self.cfg.messages.typo_probability:
            summary = self._inject_typo(summary)

        return re.sub(r"\s+", " ", summary).strip()
