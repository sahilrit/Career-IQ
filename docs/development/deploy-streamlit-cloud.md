# Deploying the dashboard to Streamlit Community Cloud

Streamlit Community Cloud (free) hosts `careeros-dashboard` as a
persistent, bookmarkable URL, no terminal needed after setup.

**Main file path** to give Streamlit Cloud:
`packages/careeros-dashboard/src/careeros_dashboard/app.py`

## Why the root `pyproject.toml` declares a dependency on `careeros-dashboard`

Streamlit Cloud auto-detects a package manager by scanning the repo root.
Since this repo has a `uv.lock`, it runs plain `uv sync` (no flags) rather
than `pip install -r requirements.txt` — `requirements.txt`/`runtime.txt`
are kept as a fallback (see below) but aren't actually the path Streamlit
Cloud uses here.

Plain `uv sync`, run with no `--all-packages` flag, only installs the
*root* project's own dependencies — in a uv workspace, workspace members
aren't included by default. Our root `pyproject.toml` is a virtual project
(`package = false`, no app code of its own), so with nothing declared in
`[project.dependencies]` the earlier deploy failed with
`ModuleNotFoundError: No module named 'careeros_dashboard'`: `uv sync` had
only installed the root's dev-tooling group (pytest, ruff, ...), never
touching `packages/*`.

The fix: `pyproject.toml` declares `dependencies = ["careeros-dashboard"]`
(with `careeros-dashboard = { workspace = true }` under `[tool.uv.sources]`).
uv resolves that transitively, so plain `uv sync` now pulls in the
dashboard and every package it depends on — verified by running
`UV_PROJECT_ENVIRONMENT=<scratch dir> uv sync` (no `--all-packages`) and
confirming `careeros_dashboard` imports cleanly. Whenever
`careeros-dashboard`'s own dependencies change, run `uv lock` at the repo
root and commit the updated `uv.lock`.

## Fallback: requirements.txt / runtime.txt

Kept in case Streamlit Cloud is ever configured to use pip instead (or
for `pip install -r requirements.txt` outside Streamlit entirely):

- [`requirements.txt`](../../requirements.txt) — regenerate with:
  ```bash
  uv export --package careeros-dashboard --no-hashes --no-dev -o requirements.txt
  ```
- [`runtime.txt`](../../runtime.txt) — pins the Python version
  (`python-3.12`, matching `.python-version`).

## Data

`.careeros/` (the SQLite database) is gitignored — a Streamlit Cloud
deploy starts with an empty Career Brain, same as a fresh local install.
Nothing personal is ever committed to the repo.

## No browser automation on this deploy path

`careeros-client-acquisition` pulls in `careeros-browser` (Playwright)
transitively, but the dashboard only imports its data-access classes —
it never launches a browser — so the plain `playwright` package installs
fine with no Chromium download or apt packages required.
