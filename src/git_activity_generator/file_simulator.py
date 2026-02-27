from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

from .config import AppConfig


PY_SNIPPETS = [
    "\ndef helper_{id}(value: int) -> int:\n    \"\"\"Auto generated helper.\"\"\"\n    return value + {delta}\n",
    "\n# TODO({id}): revisit edge case handling for timezone offsets\n",
    "\nclass GeneratedService{id}:\n    def run(self) -> str:\n        return \"ok-{id}\"\n",
]

MD_SNIPPETS = [
    "\n- [{ts}] Added note on scheduler drift mitigation.\n",
    "\n## Update {id}\n\nRefined branching simulation behavior.\n",
]

JSON_SNIPPETS = [
    "\n  \"generated_flag_{id}\": true",
    "\n  \"last_run_{id}\": \"{ts}\"",
]


class FileChangeSimulator:
    def __init__(self, cfg: AppConfig, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.repo = Path(cfg.repo_path)
        self.generated = self.repo / ".activity-sim"
        self.generated.mkdir(exist_ok=True)

    def _pick_target(self) -> Path:
        candidates = list(self.repo.glob("**/*.py")) + list(self.repo.glob("**/*.md"))
        candidates = [c for c in candidates if ".git" not in c.parts and c.is_file()]
        if candidates and self.rng.random() < 0.6:
            return self.rng.choice(candidates)

        ext = self.rng.choice(["py", "md", "json", "yaml", "js"])
        return self.generated / f"module_{self.rng.randint(1, 8)}.{ext}"

    def mutate(self) -> Path:
        target = self._pick_target()
        target.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().isoformat()
        random_id = self.rng.randint(100, 999)

        if target.suffix == ".py":
            payload = self.rng.choice(PY_SNIPPETS).format(id=random_id, delta=self.rng.randint(1, 10), ts=ts)
        elif target.suffix == ".md":
            payload = self.rng.choice(MD_SNIPPETS).format(id=random_id, ts=ts)
        elif target.suffix == ".json":
            if not target.exists():
                target.write_text("{\n  \"seed\": 1\n}\n", encoding="utf-8")
            body = target.read_text(encoding="utf-8").rstrip("\n}\t ")
            payload = body + "," + self.rng.choice(JSON_SNIPPETS).format(id=random_id, ts=ts) + "\n}\n"
            target.write_text(payload, encoding="utf-8")
            return target
        elif target.suffix == ".yaml":
            payload = f"\nentry_{random_id}:\n  updated_at: '{ts}'\n  note: generated automation edit\n"
        else:
            payload = f"\nfunction generated{random_id}() {{\n  return 'auto-{random_id}';\n}}\n"

        with target.open("a", encoding="utf-8") as fh:
            fh.write(payload)
        return target
