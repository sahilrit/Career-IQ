# Local / Self-Hosted Edition

CareerOS runs entirely on your own machine or server — nothing here
requires a cloud account. This covers running it directly, running it
in Docker, and checking that an install is actually healthy.

## Running directly (Mac, Windows, Linux)

```bash
uv sync --all-packages
uv run playwright install chromium
uv run streamlit run packages/careeros-dashboard/src/careeros_dashboard/app.py
```

The dashboard and CLI both default to `.careeros/data/careeros.db`
(SQLite) for storage — no database server to install or configure. The
dashboard reads its data directory from `$CAREEROS_DATA_DIR`; the CLI
takes it as `--data-dir` (see [`careeros_cli`](../../packages/careeros-cli)).

## Running in Docker

```bash
docker compose up
```

This builds the image from the root [`Dockerfile`](../../Dockerfile) and
starts the dashboard on <http://localhost:8501>, with `.careeros` data
persisted to a named Docker volume. No other services start by default.

### Optional scale-out services

The roadmap's local-stack diagram (CareerOS + PostgreSQL + Redis + Qdrant)
describes an optional, larger deployment for scaling past SQLite — not a
requirement. Start those services explicitly if you want them:

```bash
docker compose --profile scale-out up
```

Nothing in the core platform depends on them today; Phase 53 (Multi-User
Production SaaS) is where a Postgres-backed `DocumentStore` implementation
would actually plug in behind the same interface.

## Checking an install is healthy

`careeros_self_hosted` (Phase 47) provides a real health check rather than
a static "it should work" claim:

```python
from careeros_self_hosted import SelfHostedDivision

division = SelfHostedDivision(".careeros/data")
for result in division.run_health_checks():
    print(result.check_name, result.passed, result.detail)

print("ready:", division.is_ready())
```

It checks: the data directory is writable, the SQLite store actually
works (write + read + delete), and browser automation (Playwright) and
the dashboard UI (Streamlit) are both importable. `collect_platform_info()`
reports the real OS/Python/architecture CareerOS is running on.
