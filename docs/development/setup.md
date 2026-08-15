# Development Setup

## Prerequisites

- Python 3.12+ (pinned in [`.python-version`](../../.python-version))
- [uv](https://docs.astral.sh/uv/) for dependency management and running
  everything (`pip install uv`, or see uv's install docs)
- git

No other software, accounts, or API keys are required to work on the
core platform (see [zero-cost constraint](../architecture/overview.md#critical-constraint)).

## Bootstrap

```bash
uv sync --all-packages
uv run pre-commit install
```

`uv sync` alone only installs the workspace root's own dependency group
(dev tooling); `--all-packages` also installs every package under
`packages/*` in editable mode so cross-package imports work locally.

## Everyday commands

```bash
# Run the full test suite
uv run pytest

# Run tests for a single package
uv run pytest packages/careeros-common

# Lint
uv run ruff check .

# Format (writes changes)
uv run ruff format .

# Format check only (what CI runs)
uv run ruff format --check .

# Run every pre-commit hook against the whole tree
uv run pre-commit run --all-files
```

## Adding a new package

Follow the pattern established by `packages/careeros-common`:

```
packages/<name>/
├── pyproject.toml     # [project] deps only — no ruff/pytest config here
├── src/<package_name>/
│   └── __init__.py
└── tests/
    └── test_*.py
```

Then run `uv sync --all-packages` again so the new package is installed
into the shared virtualenv and picked up by the workspace lockfile.

## Configuration

See [`careeros_common.config`](../../packages/careeros-common/src/careeros_common/config.py)
and [`config/local.yaml.example`](../../config/local.yaml.example) for how
layered configuration works. Copy `config/local.yaml.example` to
`config/local.yaml` (gitignored) for machine-local overrides — never commit
real secrets there or anywhere else in the repo.
