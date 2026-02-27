from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from .config import load_config
from .engine import ActivityEngine
from .logger import setup_logging

log = logging.getLogger(__name__)
PID_FILE = Path(".activity-generator.pid")


def cmd_simulate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    setup_logging(cfg.verbose)
    engine = ActivityEngine(cfg)
    stats = engine.simulate_day()
    print(json.dumps({"planned": stats.commits_planned, "created": stats.commits_created}, indent=2))
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    setup_logging(cfg.verbose)
    engine = ActivityEngine(cfg)
    PID_FILE.write_text(str(time.time()), encoding="utf-8")
    log.info("Starting unattended loop with %s minute interval", args.interval)
    try:
        while PID_FILE.exists():
            now = datetime.now()
            if now.hour == cfg.working_hours_start and now.minute < args.interval:
                engine.simulate_day()
            time.sleep(args.interval * 60)
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()
    return 0


def cmd_stop(_: argparse.Namespace) -> int:
    if PID_FILE.exists():
        PID_FILE.unlink()
        print("Stop signal written.")
    else:
        print("No active loop detected.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    setup_logging(cfg.verbose)
    engine = ActivityEngine(cfg)
    today = datetime.now(engine.tz).date()
    planned = engine.scheduler.planned_commits_for_day(today)
    windows = [x.when.isoformat() for x in engine.scheduler.build_windows(today, planned)]
    print(json.dumps({"date": today.isoformat(), "planned": planned, "windows": windows}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Human-like git activity generator")
    parser.add_argument("--config", default="config/config.yaml", help="Path to YAML configuration")
    sub = parser.add_subparsers(dest="command", required=True)

    simulate = sub.add_parser("simulate", help="Run one day simulation immediately")
    simulate.set_defaults(func=cmd_simulate)

    start = sub.add_parser("start", help="Start unattended loop mode")
    start.add_argument("--interval", type=int, default=15, help="Polling interval in minutes")
    start.set_defaults(func=cmd_start)

    stop = sub.add_parser("stop", help="Stop loop mode")
    stop.set_defaults(func=cmd_stop)

    report = sub.add_parser("report", help="Show planned commit schedule for today")
    report.set_defaults(func=cmd_report)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

