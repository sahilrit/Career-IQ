# Phase 1 — Repository Foundation

Status: ✅ done

## Goal

Create the engineering foundation the rest of CareerOS builds on: a
monorepo with working quality gates and nothing domain-specific yet.

## What shipped

- **Monorepo** — a [uv](https://docs.astral.sh/uv/) workspace rooted at
  [`pyproject.toml`](../../pyproject.toml), with packages under
  `packages/*`. The root project is virtual (`tool.uv.package = false`):
  it exists to define the workspace and shared tool config, not to be
  installed itself.
- **Package structure** — [`packages/careeros-common`](../../packages/careeros-common)
  is the first package and establishes the pattern every future package
  follows: `pyproject.toml` + `src/<package_name>/` + `tests/`, built with
  hatchling, installed editable into the shared workspace virtualenv.
- **Configuration system** — [`careeros_common.config`](../../packages/careeros-common/src/careeros_common/config.py)
  layers `config/default.yaml` → `config/{environment}.yaml` →
  `config/local.yaml` (gitignored) → `CAREEROS_*` environment variables,
  via `pydantic-settings`. No layer requires a paid API key or external
  service to resolve.
- **Logging** — [`careeros_common.logging`](../../packages/careeros-common/src/careeros_common/logging.py)
  gives every package a stdlib-only `get_logger()`, idempotent to call
  from multiple entry points.
- **Base exceptions** — [`careeros_common.exceptions`](../../packages/careeros-common/src/careeros_common/exceptions.py)
  defines `CareerOSError` as the root of every future package-specific
  exception hierarchy.
- **Ruff** — lint + format configured once at the workspace root
  (`[tool.ruff]` in `pyproject.toml`); package-level `pyproject.toml`
  files do not redeclare it.
- **Pytest** — configured to discover `packages/**/tests`, using
  `--import-mode=importlib` so future packages can each have a
  `tests/test_config.py` without module-name collisions.
- **pre-commit** — [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml)
  runs ruff (lint + format) plus standard hygiene hooks
  (trailing-whitespace, end-of-file-fixer, check-yaml/toml,
  check-added-large-files, check-merge-conflict) on every commit.
- **Documentation structure** — `docs/architecture`, `docs/development`,
  `docs/phases` (this roadmap and its per-phase notes).
- **Development standards** — see
  [`docs/development/standards.md`](../development/standards.md).

## Exit criteria

- `uv sync --all-packages` installs cleanly.
- `uv run ruff check .` and `uv run ruff format --check .` are clean.
- `uv run pytest` passes.
- `pre-commit run --all-files` passes.
- A git repository exists with this state as its first commit.

## Explicitly out of scope

Nothing domain-specific: no Career Brain entities, no plugin runtime, no
event bus, no providers. Those are Phase 2 onward — see
[ROADMAP.md](ROADMAP.md).
