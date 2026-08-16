# CareerOS web (Phase R1)

Next.js (App Router) + Tailwind + framer-motion frontend that consumes
`careeros-api`. Read-only surfaces for now: login/signup, dashboard,
Career Brain, Opportunities, Analytics. Writes and the full surface land
in R2.

## Run

Start the API first (from the repo root):

```bash
uv run uvicorn careeros_api:app --port 8000
```

Then the web app:

```bash
cd web
npm install
CAREEROS_API_BASE=http://localhost:8000 npm run dev
```

Open http://localhost:3000. Sign up, and you're in.

## How auth works

Login/signup call our own route handlers (`/api/auth/*`), which call the
API and store the returned bearer token in an **httpOnly cookie**. Client
JS never sees the token, and a full page refresh stays logged in (the
Streamlit limitation is gone). Server components read the cookie and call
the API directly.

## Config

- `CAREEROS_API_BASE` — the API origin (default `http://localhost:8000`).
- The API must allow this app's origin via `CAREEROS_CORS_ORIGINS`
  (default already includes `http://localhost:3000`).

## Design system

Tailwind tokens live in `tailwind.config.ts`; motion primitives in
`components/Motion.tsx`. This is where the 21st.dev component MCP and the
ui-ux-pro-max skill plug in as the UI grows.
