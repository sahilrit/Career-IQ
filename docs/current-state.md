# CareerOS — current state

Verified against the working tree on 2026-09-02 (`main`, `67ce8f6`). Every
command below was run, not copied from an older doc.

> `README.md` was rewritten and verified against this document and the code on
> 2026-09-02. The two agree; where they overlap, both were checked against the
> repository rather than against each other.

---

## 1. What it is, in one paragraph

A multi-tenant career operating system covering employment and freelance work.
The path that matters is:

```
discover  →  score  →  generate  →  review  →  open the form
                                                    │
                                    detect → map → fill → verify
                                                    │
                                   submission-ready (a human submits)
```

It deliberately stops before Submit. `scripts/e2e_smoke.py` runs that whole path
against live boards and real forms.

Results move between runs, and not only because the code changes: discovery
samples different postings, employers edit their forms, and anti-bot challenges
come and go. Treat any single run as a sample rather than a score. What the most
recent validation established is qualitative and more durable than a ratio —
every stage of the workflow executed against real postings, no generated
document contained an unsupported or disputed claim, and the runs that did not
reach submission-ready each stopped for a stated reason: a required question
only the candidate can answer, an employer that hosts no form, an anti-bot
challenge, or a genuine disqualification.

---

## 2. Project structure

Three deployable surfaces sit on top of one Python workspace:

```
CAREER IQ/
├── packages/                    67 uv workspace members (Python)
├── web/                         Next.js app — the real product UI
├── scripts/                     operational entry points
├── config/                      layered YAML (default/dev/test/prod/local)
├── docs/                        see the index below
├── Dockerfile                   Streamlit dashboard image
├── Dockerfile.api               FastAPI image
├── render.yaml                  Render: careeros-db + careeros-api + careeros-web
└── pyproject.toml               workspace root (virtual — never installed itself)
```

### The packages that carry the workflow

| Package | Role |
|---|---|
| `careeros-career-brain` | the source of truth about you. Nothing may invent a fact about you. |
| `careeros-llm` | LLM gateway — task routing, provider fallback, health, CLI providers |
| `careeros-ai` | the low-level `AIClient` seam the gateway is built on |
| `careeros-job-providers` | provider SDK: `JobPosting`, filtering, dedupe, registry |
| `careeros-ats-providers` | 9 hosted ATSes over 120 verified company boards |
| `careeros-job-search` | where all provider wiring lives — one place |
| `careeros-job-discovery` | discover → score → store → emit |
| `careeros-application-engine` | resume, cover letter, answers, ATS report, **reviewer** |
| `careeros-browser` | `BrowserSession` (Playwright) + `FakeBrowserSession` |
| `careeros-autopilot` | live-page form detection and field mapping |
| `careeros-application-runner` | fill, verify, report — `FillReport` |
| `careeros-api` | FastAPI backend — 27 routers, 96 endpoints |
| `careeros-dashboard` | Streamlit UI, 16 pages |
| `careeros-cli` | the `careeros` console command |
| `careeros-tenancy` / `-auth` / `-credentials` | isolation, login, encrypted vault |

Everything else is supporting domain surface (CRM, analytics, interview prep,
freelance, billing, offers, personal brand…).

### Job sources

- **9 hosted ATSes** — greenhouse, lever, ashby, smartrecruiters, workable,
  recruitee, personio, bamboohr, workday. These are the only ones whose forms
  can actually be filled.
- **12 aggregators** — RemoteOK, Arbeitnow, Himalayas, Jobicy, WorkingNomads,
  WeWorkRemotely, TheMuse, HiringCafe, Adzuna, GolangJobs, Seek, LinkedIn.
- **Browser-gated, local-daemon only** — Naukri, Gradcracker, UK Visa Jobs,
  ZipRecruiter, Glassdoor (need an anti-detect browser; never in the hosted image).
- **Freelance** — Fiverr, via the `FIND_GIGS` provider SDK.

### Docs index

| File | Covers |
|---|---|
| `docs/architecture/overview.md` | package map, principles |
| `docs/llm-providers.md` | routing, fallback, the CLI exit-0 trap, config |
| `docs/job-providers.md` | why ATS discovery is company-scoped, adding an ATS |
| `docs/application-engine.md` | the five fill outcomes, why read-back exists |
| `docs/career-profile.md` | the zero-fabrication rule and how it is enforced |
| `docs/testing.md` | the five test levels |
| `docs/troubleshooting.md` | symptom → cause → command |
| `docs/competitive-integration-log.md` | what was taken from the 3 external repos |

---

## 3. How to launch it

One-time:

```bash
uv sync
uv run playwright install chromium
```

### The web product (what you'd actually use)

Two processes. API first:

```bash
CAREEROS_ENV=dev uv run uvicorn careeros_api:app --reload --port 8000
```

Then the Next.js front end, pointed at it:

```bash
cd web && CAREEROS_API_BASE=http://localhost:8000 npm run dev
```

Opens on `http://localhost:3000`. Routes include `/dashboard`,
`/opportunities`, `/career-brain`, `/autopilot`, `/watchlist`, `/settings`,
`/freelance`, `/pitch-kit`, `/interview`, `/analytics`.

### The Streamlit dashboard (the older, self-contained UI)

```bash
CAREEROS_SINGLE_USER=1 uv run streamlit run packages/careeros-dashboard/src/careeros_dashboard/app.py
```

`CAREEROS_SINGLE_USER=1` removes login entirely and uses an unscoped local
store — the personal-install mode. Without it you get the multi-tenant SaaS
flow (marketing page → sign up → isolated workspace).

### The CLI

```bash
uv run careeros brain show
uv run careeros search --keywords "performance marketing,paid media"
uv run careeros generate-package --job-url "https://..."
uv run careeros applications
```

Defaults to `.careeros/data`; override with `--data-dir`.

### The autopilot daemon (real applications, local only)

Runs a real browser. Against your live Render account:

```bash
export CAREEROS_DATABASE_URL="postgres://…"   # Render → API service → External URL
uv run python scripts/autopilot_daemon.py --workspace-id <ID> --once --show-browser
```

Or the wrapper that prompts for the URL and bakes in your workspace id:

```bash
bash scripts/apply.sh
```

Without `CAREEROS_DATABASE_URL` it runs against local SQLite, offline.

### Checks you can run

```bash
uv run python scripts/e2e_smoke.py --per-ats 3      # full workflow, live boards, never submits
uv run python scripts/verify_ats_boards.py          # are all 120 company boards alive?
uv run pytest                                       # 2500 passed, 1 skipped, ~6 min
uv run pytest -m "not browser"                      # 2450 passed, 50 deselected, ~3 min
```

### Deployed

`render.yaml` defines `careeros-db` (Postgres), `careeros-api` (Dockerfile.api)
and `careeros-web` (web/Dockerfile), all on the free tier. After the first
deploy, paste the API's public URL into the web service's `CAREEROS_API_BASE`.

### Environment variables worth knowing

| Variable | Effect |
|---|---|
| `CAREEROS_SINGLE_USER=1` | no login, unscoped store (personal install) |
| `CAREEROS_DATA_DIR` | local data dir (default `.careeros/data`) |
| `CAREEROS_DATABASE_URL` | use Postgres instead of local SQLite |
| `CAREEROS_SECRET_KEY` | encrypts stored secrets. **Rotating it makes every stored key undecryptable.** |
| `CAREEROS_AI_API_KEY` | one AI key; the vendor is inferred from its shape |
| `CAREEROS_LLM_CLI_ENABLED=0` | ignore locally installed agent CLIs (set this on a server) |
| `CAREEROS_LLM_PRIORITY` | comma-separated provider ids, best first |
| `CAREEROS_ENABLE_LINKEDIN=0` | switch off the browser-reading LinkedIn source |

---

## 4. LLM provider state on this machine

```
claude-cli   available          installed, authenticated, usable
gemini-cli   not_authenticated  installed; needs GEMINI_API_KEY or ~/.gemini/settings.json
codex-cli    not_installed      npm install -g @openai/codex, then `codex login`
api-key      not_configured     set CAREEROS_AI_API_KEY, or store a key per workspace
```

**Claude is authenticated and has been exercised live** — job analysis with
structured output, cover-letter generation, and the AI half of the reviewer, all
against the real Career Brain. Fallback was observed working: a `review` task
prefers a different provider from the drafter, tried `gemini-cli`, hit its
authentication error, and fell through to `claude-cli`.

Gemini, Codex and GPT are implemented and routed to, and their states are
reported accurately, but none has been exercised end-to-end here. Implemented is
not the same as proven.

Check with:

```bash
uv run python -c "from careeros_llm import LLMGateway; [print(h.describe()) for h in LLMGateway.from_env().provider_report()]"
```

`provider_report()` covers every provider CareerOS knows about, including ones
absent from this machine — a provider missing from the list is one the user
cannot act on.

The deterministic half of the reviewer — invented employers, unsupported
figures, unearned degrees, leftover placeholders, disputed claims and figures
used without their qualification — runs regardless, with no AI.

---
