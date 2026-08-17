# Go-live runbook

Everything below is one-time, and everything that needs a login is
**yours to run** — creating accounts, entering credentials, and
provisioning paid infra can't be automated for you. Two paths: Fly.io
(single command each) or Render (dashboard). Both use the Docker images
and Postgres store already in the repo.

## 0. Prerequisites (yours)

- A GitHub account (repo already at `git@github.com:sahilrit/Career-IQ.git`).
- A Fly.io **or** Render account.
- A Stripe account (for real payments).
- A domain (optional but expected for selling).

## 1. Push so CI runs

```bash
git push origin main
```

This triggers `.github/workflows/ci.yml`: lint + tests **against a real
Postgres** and a **build of both Docker images**. Watch it green on
GitHub → this proves the Postgres store and the images before any deploy.

**Auto-deploy on green CI** — `.github/workflows/deploy.yml` runs *after*
CI succeeds on main. If you use Fly, add a `FLY_API_TOKEN` repo secret
(`fly tokens create deploy`) and it deploys the API + web automatically
on every green push. With no secret it's a clean no-op — and Render /
Vercel auto-deploy on push on their own, so you don't need the Action
there.

## 2. Free path (recommended to validate before spending anything)

**Render Blueprint** — deploys the API, a free Postgres, and the web app
from `render.yaml`, and **auto-redeploys on every push to main** (no
GitHub Action needed):

1. Render → **New → Blueprint** → pick `sahilrit/Career-IQ`. It reads
   `render.yaml` and provisions `careeros-db` (free Postgres),
   `careeros-api`, and `careeros-web`.
2. After the first build, set two values in the dashboard:
   - `careeros-web` → `CAREEROS_API_BASE` = the `careeros-api` public URL.
   - `careeros-api` → `CAREEROS_ADMIN_EMAILS` = your email.
3. Open the `careeros-web` URL, sign up, done.

Free-tier caveats (fine for validation): services sleep after ~15 min
idle (slow first request after that), and free Postgres expires after
90 days. Render's free tier is typically card-free — if a card is ever
requested it's for identity only; low usage bills $0.

**Even freer frontend (optional):** deploy `./web` to **Vercel** (free
hobby, no sleep) instead of the Render web service — import the repo, set
root directory `web`, add `CAREEROS_API_BASE`. Keep the API + Postgres on
Render. Note: every API call the web app makes is server-to-server, so
there is nothing to configure for browser CORS.

## 2A. Paid / always-on path — Deploy on Fly.io

```bash
# API
fly launch --no-deploy --config fly.api.toml --dockerfile Dockerfile.api
fly postgres create --name careeros-db
fly postgres attach careeros-db          # sets DATABASE_URL on the app
fly secrets set \
  CAREEROS_DATABASE_URL="$(fly ssh console -C 'printenv DATABASE_URL' | tr -d '\r')" \
  CAREEROS_ADMIN_EMAILS="you@yourdomain.com" \
  CAREEROS_CORS_ORIGINS="https://careeros-web.fly.dev"
fly deploy --config fly.api.toml --dockerfile Dockerfile.api

# web
cd web
fly launch --no-deploy --dockerfile Dockerfile
fly secrets set CAREEROS_API_BASE="https://careeros-api.fly.dev"
fly deploy
```

Open `https://careeros-web.fly.dev`, sign up, and you're in.

## 2B. Deploy on Render (dashboard)

1. New **PostgreSQL** → copy its internal connection string.
2. New **Web Service** from the repo, Docker, `Dockerfile.api`. Env:
   `CAREEROS_DATABASE_URL` (the Postgres string), `CAREEROS_ADMIN_EMAILS`,
   `CAREEROS_CORS_ORIGINS` (the web URL, filled after step 3),
   `CAREEROS_STRIPE_WEBHOOK_SECRET`.
3. New **Web Service** from `./web`, Docker, `web/Dockerfile`. Env:
   `CAREEROS_API_BASE` = the API service URL.
4. Go back and set the API's `CAREEROS_CORS_ORIGINS` to the web URL.

## 3. Domain + HTTPS

Point `app.yourdomain.com` → web and `api.yourdomain.com` → API (both
platforms issue TLS automatically). Update `CAREEROS_API_BASE` and
`CAREEROS_CORS_ORIGINS` to the custom domains. The session cookie is
`secure` in production, so both must be HTTPS.

## 4. Stripe

1. Create two **Payment Links** (Pro $29/mo, Agency $99/mo, recurring).
   Put them in the dashboard's billing env if you keep Streamlit, and
   they already surface on the web Billing page via the API.
2. Add a **webhook** → `https://api.yourdomain.com/webhooks/stripe`,
   event `checkout.session.completed`. Copy its signing secret into
   `CAREEROS_STRIPE_WEBHOOK_SECRET`. Paid plans then activate
   automatically (verified by the API's webhook tests).

## 5. First admin + smoke test

- Sign up with the email in `CAREEROS_ADMIN_EMAILS` → the Admin page
  appears (accounts, MRR, plan activation).
- Import your resume on Career Brain, run a job search, and confirm
  results appear. You're live.

## Bringing your existing local data (optional)

```bash
CAREEROS_DATABASE_URL="<prod postgres url>" \
  uv run python scripts/sqlite_to_postgres.py --sqlite .careeros/data/careeros.db
```
