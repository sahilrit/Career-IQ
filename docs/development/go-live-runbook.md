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

## 2A. Deploy on Fly.io

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
