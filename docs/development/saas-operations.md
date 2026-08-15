# Running CareerOS as a SaaS

CareerOS ships in two modes, chosen by environment variables. Nothing
else changes between them — same code, same database schema.

| Mode | How | Who it's for |
|---|---|---|
| **SaaS** (default) | Just run the dashboard | Selling hosted access: signup/login, per-customer isolated workspaces, plans |
| **Single-user** | `CAREEROS_SINGLE_USER=1` | Your own laptop / a self-hosted personal install — no login, original behavior |

## Environment variables

| Variable | Purpose |
|---|---|
| `CAREEROS_DATA_DIR` | Where `careeros.db` lives (default `.careeros/data`) |
| `CAREEROS_SINGLE_USER` | `1` disables auth entirely (self-hosted mode) |
| `CAREEROS_ADMIN_EMAILS` | Comma-separated emails that can open the Admin page |
| `CAREEROS_STRIPE_LINK_PRO` | Stripe Payment Link URL for the Pro tier |
| `CAREEROS_STRIPE_LINK_AGENCY` | Stripe Payment Link URL for the Agency tier |

## How accounts work

- Signup (landing page) provisions the full chain in one step: User →
  Organization → Workspace → owner Membership → **Free** subscription.
- Passwords: PBKDF2-HMAC-SHA256 (600k iterations, stdlib only), policy
  enforced by `careeros_compliance.SecurityPolicy` (12+ chars,
  uppercase, digit, symbol). 5 failed logins lock the account 15 minutes.
- Sessions: 7-day server-side tokens; only the SHA-256 hash is stored.
  Changing a password revokes every session.
- Isolation: every page reads/writes through `TenantScopedDocumentStore`,
  so customer A can never see customer B's data. This is covered by
  tests (`test_auth_flow.py::test_two_accounts_are_tenant_isolated`).

## Taking payments

Payments use **Stripe Payment Links** — no Stripe SDK, no secret key in
the app, consistent with the platform's zero-mandatory-paid-dependency
rule.

1. In the Stripe dashboard, create two Payment Links (Pro $29/mo,
   Agency $99/mo, recurring).
2. Set `CAREEROS_STRIPE_LINK_PRO` / `CAREEROS_STRIPE_LINK_AGENCY`.
   The Billing page then shows Upgrade buttons.
3. When a customer pays, activate their plan on the **Admin** page
   ("Activate a plan"). Match them by the email Stripe gives you.

A webhook-driven activator can replace step 3 later without touching
plan/subscription code — `SubscriptionRepository` is the only writer.

## Admin page

Set `CAREEROS_ADMIN_EMAILS=you@yourdomain.com`, sign up with that email,
and the Admin page shows accounts, paying workspaces, MRR, and the
plan-activation form.

## Migrating a pre-SaaS database

Data written before auth existed is unscoped and invisible to SaaS-mode
accounts. Either keep running that install with `CAREEROS_SINGLE_USER=1`,
or claim the data for one workspace:

```bash
uv run python scripts/migrate_to_workspace.py --workspace-id <ID> --dry-run
uv run python scripts/migrate_to_workspace.py --workspace-id <ID>
```

(Your workspace id is shown on the Admin page after signup.)

## Deploying

- **Docker**: `docker compose up` — set the env vars in
  `docker-compose.yml` or an `.env` file. The volume keeps `careeros.db`.
- **Streamlit Community Cloud**: works as before (`requirements.txt` is
  the export of the dashboard package); set the env vars in the app's
  Secrets settings.
- SQLite is fine for one node. Before scaling to multiple instances,
  put the DocumentStore on Postgres (the interface was designed for a
  drop-in swap — see `careeros_common/storage.py`).
