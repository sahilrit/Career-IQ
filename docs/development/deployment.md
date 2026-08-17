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
