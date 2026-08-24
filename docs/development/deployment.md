# Deploying CareerOS for real customers

CareerOS runs in two storage modes, chosen by one environment variable:

| Mode | How | For |
|---|---|---|
| **SQLite** (default) | nothing set | local dev, single-node self-hosting |
| **Postgres** | `CAREEROS_DATABASE_URL=postgresql://…` | multi-node production |

Both back the exact same `(entity_type, id) -> JSON` document store, so
no domain code changes between them — only the env var. See
`careeros_common.open_store`.

## What runs where

- **Postgres** — the source of truth. Any managed Postgres works (Fly
  Postgres, Render, Supabase, RDS, Neon).
- **API** (`careeros-api`, FastAPI) — `Dockerfile.api`. The backend the
  React app calls; also serves the Stripe webhook. Needs
  `CAREEROS_DATABASE_URL`.
- **web** (`web/`, Next.js) — `web/Dockerfile`. Needs `CAREEROS_API_BASE`
  pointing at the API's public URL.
- **dashboard** (Streamlit) — optional; the original UI, same Postgres.

## Fastest path: docker compose on one box

```bash
cp .env.prod.example .env      # fill in POSTGRES_PASSWORD, admin email, domains
docker compose -f docker-compose.prod.yml up --build
```

Postgres, API (`:8000`), and web (`:3000`) come up; add
`--profile dashboard` for Streamlit (`:8501`). Put a reverse proxy that
terminates HTTPS (Caddy/Traefik/nginx) in front, mapping
`app.yourdomain.com -> web:3000` and `api.yourdomain.com -> api:8000`.

## PaaS path (Fly.io / Render)

Deploy two services from the same repo:

1. **API**: build `Dockerfile.api`; set `CAREEROS_DATABASE_URL` (managed
   Postgres), `CAREEROS_ADMIN_EMAILS`, `CAREEROS_CORS_ORIGINS`
   (your web origin), `CAREEROS_STRIPE_WEBHOOK_SECRET`.
2. **web**: build `web/Dockerfile`; set `CAREEROS_API_BASE` to the API's
   public URL.

Point your domain at web, and a subdomain at the API. HTTPS is handled
by the platform. The httpOnly session cookie is `secure` in production,
so both must be served over HTTPS.

## Stripe

Create a webhook in Stripe → `https://api.yourdomain.com/webhooks/stripe`,
copy its signing secret into `CAREEROS_STRIPE_WEBHOOK_SECRET`. On
`checkout.session.completed` the plan activates automatically (no manual
Admin step). Keep the Payment Links in the dashboard's billing env vars.

## Optional job-source keys

Most discovery providers are free public APIs that need no configuration.
Two sources take optional environment variables; set them on the **API**
service (the same place as `CAREEROS_DATABASE_URL`).

### Adzuna (official multi-country jobs API)

Adzuna is the highest-volume legitimate source in the pool, covering 20+
countries. It stays dormant until both keys are present — with neither, the
provider reports itself unavailable and the other sources carry on, so an
install that never sets these loses nothing.

1. Register a free application at <https://developer.adzuna.com>. The
   dashboard shows your **Application ID** and **Application Key**.
2. On the `careeros-api` service, add:

   | Variable | Value |
   |---|---|
   | `ADZUNA_APP_ID` | your Application ID |
   | `ADZUNA_APP_KEY` | your Application Key |

3. Save. Render (or your platform) redeploys the API, and Adzuna joins the
   next search automatically — no code change.

**Verify:** run one Opportunities search for a real city (e.g. "London",
"New York"). Adzuna results should appear alongside the others. If it stays
quiet, the search form's amber "a source didn't respond" notice reports
exactly what Adzuna returned, so a wrong key surfaces plainly rather than
failing silently. The provider infers the Adzuna country from the searched
location (defaulting to Great Britain when none is given).

### LinkedIn (public logged-out search)

LinkedIn is **on by default** and reads the public guest search endpoint
from whichever host runs the search — so on a hosted deploy the traffic
comes from your server's IP. It is throttled (~1 request/second) and caps
description fetches per search. If you ever see rate limiting, set
`CAREEROS_ENABLE_LINKEDIN=0` on the API service to switch it off; the other
sources are unaffected.

## Free-tier spin-down (Render) — accepted limitation, not fixed

Render's free instance type spins down after ~15 min with no incoming
HTTP traffic, adding a ~50s cold start to the next request. This is
**not currently prevented** for either service; both `careeros-api` and
`careeros-web` can go cold. Two things were tried and neither reliably
stops it:

1. **`.github/workflows/keepalive.yml`** — a GitHub Actions cron that
   curls both services every 10 min. GitHub's scheduled-workflow
   triggers are best-effort, not exact: observed firing 1–4 hours apart
   despite the 10-min cron, so it does not reliably beat the 15-min
   spin-down window.
2. **Render's own Health Check Path** (Settings → Health Checks, per
   service; `careeros-api` → `/health`, `careeros-web` →
   `/api/health`, added in `web/app/api/health/route.ts`) — verified
   empirically (2026-08-25) that this does **not** prevent free-tier
   idle spin-down: a `careeros-web` instance died from inactivity at
   the standard 15-minute mark with the health check path correctly
   configured. `careeros-api` staying continuously warm in the logs
   turned out to be explained by other real traffic hitting it (not
   proof the health check path itself keeps a service alive) — don't
   trust that pattern as a working fix.

If this cold start becomes a real problem, the two options that would
actually solve it are a genuine external uptime monitor (e.g.
UptimeRobot, cron-job.org) hitting the public URL on a tight schedule,
or a paid Render instance type (which removes free-tier spin-down
entirely). Neither is set up as of this writing.

**Reading the logs:** on `careeros-web`'s Logs tab, an
`npm error ... signal SIGTERM` block appears both on an ordinary deploy
cutover (harmless — old instance replaced by new, "Deploying..."
appears right around it) and on an idle spin-down (the instance simply
stops, with a gap in the logs until the next request wakes it) — the
deploy-events list on the same tab tells you which one you're looking
at. `careeros-api` logs every request (FastAPI/uvicorn), so continuous
`GET /health` 200s there just mean *something* is currently calling it
— not that any particular mechanism is guaranteed to keep doing so.

## Migrating existing SQLite data to Postgres

A tiny one-time copy (both stores share the schema): read every row from
`.careeros/data/careeros.db` and `put` it into Postgres.

```bash
CAREEROS_DATABASE_URL=postgresql://…  # target
uv run python scripts/sqlite_to_postgres.py --sqlite .careeros/data/careeros.db
```

## Notes / limits

- The Postgres store uses a connection pool (thread-safe under the API's
  concurrency); SQLite uses a single shared connection (fine for one node).
- The autopilot daemon and Streamlit dashboard both read the same
  `CAREEROS_DATABASE_URL`, so they operate on the same production data.
