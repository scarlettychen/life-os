# LifeOS

A personal AI Chief of Staff — a decision engine that understands your entire workload
(school, robotics, ISEF/research, competitions, personal goals) and helps you decide how
to spend your time.

> Full design spec lives in the Obsidian vault: `AI-Vault/02-Projects/Life-OS/`.

This repository is the code. It is being built in milestones (see the roadmap). This is
**M0 — Foundations**: project structure, database models, and CRUD for tasks, goals,
and projects.

## Requirements

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
uv sync                 # create venv + install deps
uv run lifeos init      # create the local SQLite database
```

## Usage (CLI)

```bash
# Areas (life domains: school, robotics, isef, ...)
uv run lifeos area add robotics --name "Competitive Robotics" --target 0.3
uv run lifeos area list

# Goals
uv run lifeos goal add "Win State Championship" --area robotics --horizon long --priority 5
uv run lifeos goal list

# Projects
uv run lifeos project add "Swerve Drivetrain" --area robotics --goal 1 --effort 40
uv run lifeos project list

# Tasks
uv run lifeos task add "Finish CAD for module v2" --project 1 --estimate 120 --energy high --deep
uv run lifeos task list
uv run lifeos task list --status todo
uv run lifeos task done 1 --actual 135
uv run lifeos task show 1
uv run lifeos task rm 1
```

## Development

```bash
uv run pytest           # run the test suite
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy             # type-check
```

## Project layout

```
src/lifeos/
  config.py           # pydantic-settings configuration
  db/engine.py        # engine + session management
  models/             # SQLModel tables (Area, Goal, Project, Task) + enums
  repositories/       # data-access layer (CRUD)
  cli.py              # Typer CLI
tests/                # pytest suite (models, repositories, CLI)
```

## Roadmap

- **M0 (this):** foundation — models + CRUD.
- **M1:** decision core — task ranking, overload detection.
- **M2:** Obsidian ingestion.
- **M3:** scheduling + rest recommendations.

See the spec for the full M0–M6 plan.
