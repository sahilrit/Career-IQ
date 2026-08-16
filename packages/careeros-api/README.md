# careeros-api — HTTP backend (Phase R0)

FastAPI over the CareerOS domain packages. This is the backend the
React/Next frontend will consume (see `docs/plans/react-frontend.md`).
Thin controllers only — no business logic lives here.

## Run

```bash
uv run uvicorn careeros_api:app --reload --port 8000
```

- Interactive docs: `http://localhost:8000/docs`
- Health: `GET /health`

Reads the same database as the dashboard (`CAREEROS_DATA_DIR`).

## Auth

The bearer token is the opaque, server-side session token from
`careeros_auth` — expiring AND revocable (safer than a stateless JWT).

```
POST /auth/signup   {email, password, full_name}   -> {token}
POST /auth/login    {email, password}               -> {token}
GET  /auth/me       (Authorization: Bearer <token>) -> account
POST /auth/logout
POST /auth/reset/request  {email}
POST /auth/reset/confirm  {token, new_password}
```

Send `Authorization: Bearer <token>` on protected routes. Every request
is resolved to a workspace and served a tenant-scoped store, so accounts
are isolated exactly as in the dashboard.

## Domain (read; more arrives in later phases)

```
GET /brain           -> the workspace's Career Brain (404 if none)
GET /applications    -> all application records
```

## Stripe webhook (replaces manual plan activation)

```
POST /webhooks/stripe
```

On `checkout.session.completed` it reads the customer email and the plan
(`metadata.plan`, or inferred from `amount_total`) and sets that
workspace's subscription tier. Set `CAREEROS_STRIPE_WEBHOOK_SECRET` to
enforce signature verification (stdlib HMAC — no Stripe SDK).

## Config

`CAREEROS_DATA_DIR`, `CAREEROS_ADMIN_EMAILS`, `CAREEROS_CORS_ORIGINS`
(comma-separated; default `http://localhost:3000`),
`CAREEROS_STRIPE_WEBHOOK_SECRET`.
