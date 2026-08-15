# Deploying the dashboard to Streamlit Community Cloud

Streamlit Community Cloud (free) hosts `careeros-dashboard` as a
persistent, bookmarkable URL, no terminal needed after setup. It
installs with plain `pip`, not `uv`, so the repo carries two extra
root-level files just for this:

- [`requirements.txt`](../../requirements.txt) — regenerate with:
  ```bash
  uv export --package careeros-dashboard --no-hashes --no-dev -o requirements.txt
  ```
  Re-run this and commit the result whenever `careeros-dashboard`'s
  dependencies change (new package, new PyPI dependency, version bump).
- [`runtime.txt`](../../runtime.txt) — pins the Python version Streamlit
  Cloud provisions (`python-3.12`, matching `.python-version`).

**Main file path** to give Streamlit Cloud:
`packages/careeros-dashboard/src/careeros_dashboard/app.py`

**Data**: `.careeros/` (the SQLite database) is gitignored — a Streamlit
Cloud deploy starts with an empty Career Brain, same as a fresh local
install. Nothing personal is ever committed to the repo.

**No browser automation on this deploy path**: `careeros-client-acquisition`
pulls in `careeros-browser` (Playwright) transitively, but the dashboard
only imports its data-access classes — it never launches a browser — so
the plain `playwright` pip package installs fine with no Chromium
download or apt packages required.
