# Development Standards

These rules apply to every package in the monorepo, from Phase 1 onward.
They exist to keep 60 phases of work from turning into 60 different
styles of code.

## Zero-cost core

No package under `packages/*` that is part of the core platform may
*require* a paid API key, paid service, or paid model to import, start, or
pass its tests. Optional paid integrations are plugins that degrade
gracefully (or are skipped) when no credential is configured — never a
hard dependency. See [`docs/architecture/overview.md`](../architecture/overview.md#critical-constraint).

## Package boundaries

- Shared, cross-cutting code (config, logging, base exceptions, common
  types) lives in `careeros-common`. Domain packages depend on it; it
  never depends on them.
- A package must not reach into another package's internals
  (`careeros_x._internal`-style modules). Depend on the public API
  (`__init__.py` exports) only.
- Prefer the event bus (Phase 4 onward) over direct imports for
  agent-to-agent or plugin-to-plugin communication. Direct imports are for
  layering (a domain package depending on `careeros-common`), not for
  peer coordination.

## Errors

Every package-specific exception subclasses `careeros_common.CareerOSError`
(directly or via an intermediate package-level base, e.g. a future
`CareerBrainError`). Do not raise bare `Exception` or built-in exception
types across a package's public API boundary.

## Configuration

New config keys are added to `config/default.yaml` (and overridden per
environment if needed), not hardcoded, not read directly from
`os.environ` inside domain code. Domain code depends on
`careeros_common.get_settings()` (or a package-specific settings model
that composes it), so every setting has one resolution path.

## Testing

- Every package ships its own `tests/` directory; `uv run pytest` from the
  repo root runs all of them.
- Tests must not depend on network access, a paid API, or credentials
  being present. Mock or fake external systems; if a test cannot run
  without a real paid dependency, it does not belong in the default test
  run.
- A bug fix gets a regression test. A new capability gets tests for its
  golden path and its documented edge cases — not exhaustive coverage of
  hypothetical inputs.

## Style

- Ruff is the only linter/formatter; its config lives once, at the
  workspace root (`pyproject.toml`). Do not add per-package Ruff config
  unless a package genuinely needs an exception, and prefer a scoped
  `# noqa` over a blanket rule disable.
- Type hints on public function signatures. Prefer `from __future__ import
  annotations` plus stdlib generics (`list[str]`, `X | None`) over
  `typing.List`/`typing.Optional`.
- Comments explain *why*, not *what*. If removing a comment wouldn't
  confuse a future reader, don't write it.
- No speculative abstraction. Build what the current phase's exit
  criteria require; don't design interfaces for a phase that hasn't
  started.

## Commits

- Conventional, imperative subject lines (`Add`, `Fix`, `Refactor`, not
  `Added`/`Fixes`).
- A commit that completes a roadmap phase should say so
  (`Phase N: <short description>`), matching the style already used in
  [`docs/phases/ROADMAP.md`](../phases/ROADMAP.md).
- Quality gates (`ruff check`, `ruff format --check`, `pytest`,
  `pre-commit run --all-files`) pass before a commit lands on the primary
  branch.
