# React/Next premium frontend — implementation plan

Status: **plan (no code yet)**. This is the track for replacing the
Streamlit UI with a production React/Next.js app. It is a multi-phase
effort; each phase ships independently and Streamlit keeps working
until parity is reached.

## Why this needs a plan, not a page

The current UI is Streamlit — Python that renders server-side. React
tools like framer-motion, the 21st.dev component MCP, and the
ui-ux-pro-max skill can't touch it. Moving to React means the Python
domain packages (career-brain, autopilot, freelance, billing, auth, the
providers) stop being imported directly by the UI and instead sit
behind an **HTTP API**. That API layer is the real work; the React app
is a client of it.

## Target architecture

```
Next.js (React) app   ──HTTP/JSON──▶   FastAPI service   ──▶  careeros_* Python packages
   (Vercel/Node host)                    (same repo)             (unchanged domain logic)
                                              │
                                              ▼
                                     DocumentStore (SQLite → Postgres)
```

- **Backend: a new `careeros-api` package** (FastAPI). Thin controllers
  that call the existing domain packages — no business logic moves. One
  router per domain: `/auth`, `/brain`, `/opportunities`, `/autopilot`,
  `/freelance`, `/billing`, `/analytics`, `/admin`.
- **Auth: JWT** issued by `careeros-auth` on login (reuse the existing
  `AuthService`; add a JWT wrapper around the session token). The React
  app stores it in an httpOnly cookie — this also fixes the current
  "refresh logs you out" problem for free.
- **Tenancy: unchanged.** Every request resolves the workspace from the
  token and hands routers a `TenantScopedDocumentStore`, exactly as the
  Streamlit `require_account()` does today.
- **Frontend: Next.js (App Router) + Tailwind + framer-motion.** Use the
  21st.dev MCP + ui-ux-pro-max skill for component generation and the
  design system.

## Phasing (each phase is shippable)

**Phase R0 — API foundation.** New `careeros-api` FastAPI app. Auth
endpoints (`/auth/signup|login|logout|reset`), JWT issuance, tenant
middleware, OpenAPI schema. Contract tests. Streamlit untouched.

**Phase R1 — read-only React shell.** Next.js app, login + JWT cookie,
and the read surfaces first: dashboard KPIs, Career Brain view,
Opportunities list, Analytics. Proves the whole stack end to end.

**Phase R2 — write surfaces.** Career Brain editing, job search,
one-click application generation, Freelance prospect audit + pitch kit,
Offers, Network. This reaches feature parity with the Streamlit app.

**Phase R3 — autopilot + realtime.** Autopilot run + live run history
(server-sent events or polling), Billing/Stripe, Admin.

**Phase R4 — polish + cutover.** framer-motion transitions, mobile,
dark mode, marketing landing page (see item #33). Flip the default UI to
React; keep Streamlit available at `/legacy` for one release, then
retire it.

## Dependencies / setup this track needs

- Add the 21st.dev component MCP: `claude mcp add --transport http 21st https://21st.dev/api/mcp --header "x-api-key: …"`.
- Node/pnpm toolchain and a Next.js host (Vercel is the natural fit;
  the FastAPI service deploys next to Postgres — see the deployment doc).
- Postgres (Bundle A item) should land before or with R1 so the API is
  multi-node ready.

## Explicit non-goals / guardrails (carried over)

- No LinkedIn/Indeed automation, no scraping of people, no
  bot-detection evasion — same as the rest of the product.
- The domain packages are the source of truth; the API must not
  reimplement logic, only expose it.

## Rough size

R0–R2 are the bulk (the API surface + parity). R3–R4 are incremental.
This is a multi-session build; do not attempt it in one pass. Start with
R0 (the FastAPI foundation) as its own reviewed change.
