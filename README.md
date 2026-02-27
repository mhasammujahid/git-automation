# Git Activity Automation Generator

Production-style Python automation toolkit that simulates human-like development activity and pushes realistic commit history to a Git repository.

## Project Overview

This project provides a modular automation engine for generating realistic daily Git commit activity with:

- Configurable scheduling (random, Gaussian, seasonal, weekend-aware, vacation-aware)
- Intelligent commit messages (categories, Conventional Commits, optional emoji, Markov variations)
- Real file mutations (non-empty commits across `.py`, `.md`, `.json`, `.yaml`, `.js`)
- Branching and merge flow simulation (feature/hotfix/squash/no-ff)
- Safety controls (daily caps, cooldown days, dry-run mode)
- CLI for unattended operation (`start`, `stop`, `simulate`, `report`)

> ⚠️ Use responsibly and in compliance with platform terms and your organization policies.

## Architecture Diagram (Text)

```text
+---------------------+
| CLI (argparse)      |
| start/simulate/...  |
+----------+----------+
           |
           v
+---------------------+
| ActivityEngine      |
| orchestration       |
+--+-------+-------+--+
   |       |       |
   v       v       v
Scheduler Message  FileChange
Engine    Generator Simulator
   |                   |
   +--------+----------+
            v
       GitService
   (branch/commit/merge/push)
            |
            v
        Target Repo
```

## Folder Structure

```text
.
├── config/
│   └── config.example.yaml
├── src/
│   └── git_activity_generator/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── engine.py
│       ├── file_simulator.py
│       ├── git_ops.py
│       ├── logger.py
│       ├── messages.py
│       └── scheduler.py
└── requirements.txt
```

## Setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml  # or create config/config.json from the JSON example
```

Edit `config/config.yaml` and set:
- `repo_path`
- activity ranges
- timezone
- branch options
- authors

## Usage

> Run from repository root.

```bash
PYTHONPATH=src python -m git_activity_generator.cli --config config/config.json report
PYTHONPATH=src python -m git_activity_generator.cli --config config/config.json simulate
PYTHONPATH=src python -m git_activity_generator.cli --config config/config.json start --interval 15
PYTHONPATH=src python -m git_activity_generator.cli --config config/config.json stop
```

### Command Behavior

- `simulate`: generate one day of commits now.
- `report`: preview today's planned commit windows.
- `start`: unattended polling loop suitable for service/daemon wrapping.
- `stop`: writes local stop signal by removing pid file.

## Deployment & Automation

### Cron (Linux/macOS)

Run once every morning in dry-run off mode:

```cron
5 9 * * * cd /path/to/git-automation && /path/to/venv/bin/python -m git_activity_generator.cli --config config/config.json simulate >> logs/activity.log 2>&1
```

### Windows Task Scheduler

Program:

```text
python
```

Arguments:

```text
-m git_activity_generator.cli --config config\config.json simulate
```

Start in:

```text
C:\path\to\git-automation
```

### Docker (example)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY config ./config
CMD ["python", "-m", "git_activity_generator.cli", "--config", "config/config.yaml", "simulate"]
```

## Advanced Features Implemented

- Gaussian commit frequency model
- Seasonal monthly multiplier
- Vacation blackout ranges
- Random cooldown (no activity) days
- Late-night commits and pre-weekend spikes
- Typo injection probability for realism
- Markov-chain message mutation
- Multi-author commit identity simulation
- Feature/hotfix branch lifecycle and merge style randomness

## Deterministic Testing Mode

Set `deterministic_seed` in config for repeatable scheduling/message output.

## Config Template

See `config/config.example.yaml` (YAML) and `config/config.json` (JSON fallback) for parameters.
