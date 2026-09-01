# CareerOS

An AI career operating system: it finds jobs, works out which are worth your
time, writes the application, fills the employer's form — and then stops and
hands it to you.

```
discover → deduplicate → score → tailor résumé → cover letter → answer questions
                                        ↓
                        deterministic QA → AI QA (independent reviewer)
                                        ↓
                     open form → detect → map → fill → read back → validate
                                        ↓
                          SUBMISSION-READY — a human reviews and submits
```

**CareerOS never clicks the final Submit button.** That is a design decision,
not a missing feature. An automated system that submits on your behalf can send
a wrong answer to an employer with no way to take it back.

The second design decision matters just as much: **CareerOS will not invent
anything about you.** Every figure in a generated document is checked back
against your career profile, and a claim the profile cannot support is withheld
even when that makes the document weaker. A question it cannot answer truthfully
comes back to you as a question, never as a plausible guess.

---

## Current capabilities

Verified against the working tree, the test suite, and live runs against real
job boards. Anything partial or blocked is marked as such.

| Area | State | Notes |
|---|---|---|
| Job discovery | Working | 9 hosted ATSes over 120 verified company boards, plus 12 aggregators |
| Normalization + dedupe | Working | one `JobPosting` schema; within-provider and cross-provider dedupe |
| Scoring | Working | deterministic heuristic; an LLM second pass is optional enrichment, never required |
| Career Brain | Working | structured profile with per-claim provenance |
| LLM gateway | Working | task routing, provider fallback, health, structured output |
| Résumé tailoring | Working | deterministic; unsupported claims excluded |
| Cover letters | Working | template always; AI-written when a provider is available |
| Application answers | Working | rule-based over profile facts, with confidence levels |
| Provenance / anti-fabrication | Working | unsupported and disputed claims blocked from all generated material |
| Deterministic QA | Working | runs with no AI configured at all |
| AI QA | Working | verified live against Claude; independent second opinion |
| ATS detection + form filling | Partial | see [Supported ATSes](#supported-atses--browser-automation) |
| Read-back validation | Working | every field written is read back; a silent rejection is a reported failure |
| Readiness + recommendation | Working | separates "the form is fillable" from "you should apply" |
| API | Working | FastAPI, 27 routers, 96 endpoints |
| Web app | Working | Next.js, the primary product surface |
| CLI | Working | `careeros brain / search / generate-package / applications` |
| Autopilot daemon | Local only | drives a real browser; never in the hosted image |
| Streamlit dashboard | Working | 16 pages; the older self-contained UI |

---

## LLM support

CareerOS talks to models through one seam — `careeros-llm`. Business logic asks
for a **task** (`classify`, `extract`, `analyze`, `write`, `answer`, `review`)
and the gateway decides which provider serves it. Nothing outside that package
names a vendor, which is what keeps CareerOS from becoming permanently dependent
on one model.

Two kinds of provider are supported: an **API key** (vendor inferred from the
key's shape) or a **locally authenticated agent CLI**. The CLI path is why the
product does not require anyone to buy an API key — if you already pay for
Claude or Gemini, that subscription is a working provider.

| Provider | Implemented | Live-tested here | Requires |
|---|---|---|---|
| Claude (`claude` CLI) | Yes | **Yes** — job analysis, cover letters, structured output and the AI reviewer all exercised against it | `claude` installed and logged in |
| Gemini (`gemini` CLI) | Yes | No — detected and routed to, but never authenticated on this machine | `GEMINI_API_KEY` or an auth method in `~/.gemini/settings.json` |
| Codex (`codex` CLI) | Yes | No — not installed here, so the adapter is unexercised | `codex` installed and `codex login` |
| GPT / OpenAI (API key) | Yes | No — no key was configured | `CAREEROS_AI_API_KEY`, or a key stored per workspace |

Be clear about what that table says: **only Claude has been exercised
end-to-end.** The other three are implemented and routed to, and the gateway
reports their state accurately, but "implemented" is not "proven".

### Provider states

A single generic "failed" made *"installed but never logged in"* and *"never
installed"* indistinguishable, leaving no way to act on either. Health reports
installed, authenticated and usable separately, with a remedy:

```
claude-cli   installed=True  auth=True   usable=True   available
gemini-cli   installed=True  auth=False  usable=False  not_authenticated
codex-cli    installed=False auth=None   usable=False  not_installed
api-key      installed=None  auth=None   usable=False  not_configured
```

### Fallback

Verified live: a `review` task prefers a *different* provider from the one that
drafted (an independent reviewer should not inherit the drafter's blind spots),
so it tried `gemini-cli` first, hit the authentication error, and fell through to
`claude-cli`, which answered. Failures are classified as retryable or not — a
timeout is worth retrying, "you are not logged in" never is.

If no provider is available at all, AI features degrade to their deterministic
equivalents. They never fabricate a response to fill the gap.

### Safety note

These CLIs are **agents**, not text completers. Left at their defaults they can
run shell commands and edit files. CareerOS sends them job descriptions fetched
from the open internet — attacker-controlled input — so every CLI is invoked
with its tools switched off (`--disallowed-tools …` for Claude, `--sandbox
read-only` for Codex).

---

## Job discovery

Hosted ATSes have no global search API. Greenhouse cannot tell you "every
Greenhouse job matching growth marketer" — so discovery is **company-scoped**:
you crawl boards you have named. That is a fact about how these systems work,
not a limitation of the implementation, and it is why `careeros-ats-providers`
ships an explicit board list rather than a search abstraction.

- **9 hosted ATSes** — Greenhouse, Lever, Ashby, SmartRecruiters, Workable,
  Recruitee, Personio, BambooHR, Workday, across **120 verified company boards**.
  These are the only sources whose forms can actually be filled.
- **12 aggregators** — RemoteOK, Arbeitnow, Himalayas, Jobicy, WorkingNomads,
  WeWorkRemotely, TheMuse, HiringCafe, Adzuna, GolangJobs, Seek, LinkedIn.
- **Browser-gated, local daemon only** — Naukri, Gradcracker, UK Visa Jobs,
  ZipRecruiter, Glassdoor. These need an anti-detect browser and are never part
  of the hosted image.
- **Freelance** — Fiverr, through the same provider SDK.

Relevance is title-anchored rather than full-text. Matching keywords anywhere in
a description kept 987 of 2,170 live Lever postings, including a "Liquor Store
Associate" whose body mentioned "performance" once in boilerplate. A description
hit only counts for multi-word phrases.

Deduplication handles two different problems: the same posting twice from one
provider, and the same *job* reached from an aggregator and from the ATS hosting
it. The second has no shared id and is the duplicate you actually notice.

---

## Application workflow

```
Discovery → qualification → Career Brain → résumé → cover letter → answers
   → deterministic QA → AI QA → ATS detection → form mapping → filling
   → read-back → validation → submission readiness
```

**CareerOS does not automatically click final Submit. You review and submit.**

### Readiness is not a recommendation

These are different questions and were once the same field, which was dangerous.
A form can be perfectly fillable for a job you must not apply to.

| Status | Meaning |
|---|---|
| `READY_TO_APPLY` | Fillable, and nothing rules you out. The only state where submitting is appropriate. |
| `SUBMISSION_READY_BUT_DISQUALIFIED` | The form was completed — but the employer explicitly rules you out. **Do not apply.** |
| `NEEDS_USER_INPUT` | Reached the form; something required is missing that only you can supply. |
| `BLOCKED` | Could not complete the form at all — no form, an anti-bot wall, a login requirement. |

A real example from a live run: an Ashby posting reached 83% form readiness with
every required field filled, while being explicitly restricted to US-based
candidates. It reports:

```
DO NOT APPLY — JOB DISQUALIFICATION
  role is restricted to US-based candidates
Form readiness: 83%
```

Anything driving a submit button asks `may_submit`, which is true **only** for
`READY_TO_APPLY`. Technical readiness never overrides a disqualification.

---

## Supported ATSes / browser automation

"Supported" means different things per ATS, so they are listed individually.
Discovery health and application health are tracked separately —
`careeros_ats_providers.capability_table()` prints the current matrix.

| ATS | Discovery | Application | Detail |
|---|---|---|---|
| Ashby | Working | **Automated** | Forms detected, filled and verified in live runs |
| Workable | Working | **Automated** | Live runs reached submission-ready |
| Lever | Working | Partial | Forms fill; some radio/select groups fail to set (see limitations) |
| Greenhouse | Working | Partial | Boards hosted on `greenhouse.io` fill; many customers route applications to their own careers site |
| SmartRecruiters | Working | Partial | The form is in an iframe — supported and verified against fixtures. Live apply pages currently serve an anti-bot challenge |
| Workday | Working | **Discovery only** | Requires an account before the form is reachable; CareerOS never creates accounts |
| Recruitee, Personio, BambooHR | Working | Unverified | Adapters exist; no live form has been driven, so they are not counted as working |

Things that are **not defects**:

- **Employer redirects.** A Greenhouse customer sending applicants to its own
  site is an employer choice. It is reported as `EXTERNAL_UNSUPPORTED`, not as a
  failure, and is excluded from application-coverage numbers.
- **Anti-bot challenges.** Cloudflare Turnstile and DataDome are detected and
  reported so a human can take over. CareerOS does not try to defeat them.
- **Workday's account requirement.** Creating accounts on someone's behalf is
  out of scope.
- **Required questions CareerOS cannot answer.** Leaving them for you is the
  intended behaviour.

`UNVERIFIED` never counts as working. An integration nobody has driven against a
live form is a claim, not a capability.

---

## Career Brain and the evidence system

The Career Brain is the structured profile everything else reads from — and,
critically, it is the authority the fabrication checker measures drafts against.
That makes an unsupported figure stored in it worse than useless: it *launders*
the figure, because the checker built to catch invented numbers would see it as
corroboration.

So every claim carries provenance:

| Status | Meaning |
|---|---|
| `VERIFIED` | Primary evidence exists |
| `DERIVED` | Computed from verified data; the derivation is retained so it can be re-checked |
| `CONFLICTING` | Sources disagree and the source material cannot settle it. Never published |
| `UNSUPPORTED` | No source supports it. Kept in your records, never published |
| `UNKNOWN` | Not audited. Publishable — absence of an audit is not evidence of a problem |

Three mechanisms enforce it:

1. **Generators skip** `CONFLICTING` and `UNSUPPORTED` claims. They stay in your
   profile — it is your record — but never reach an employer.
2. **The fabrication checker excludes them** from what it treats as true, so a
   draft quoting one is flagged exactly like an invented figure.
3. **Qualifiers must travel with their figure.** Some numbers are true only when
   qualified — booked versus delivered revenue, a peak month versus a typical
   one. A claim can require specific wording, and a draft that uses the figure
   without it is rejected. The number is real; the claim would not be.

Answers carry confidence — `HIGH` (a verified profile fact), `MEDIUM` (derived or
generated), `LOW` (a defensible default), `UNKNOWN` (cannot be answered
truthfully). Anything `UNKNOWN` comes back as `NEEDS_USER_INPUT` with the reason
and what would resolve it. Once you answer, it is remembered.

---

## Architecture

```
CAREER IQ/
├── packages/          67 uv workspace members (Python)
├── web/               Next.js app — the primary product UI
├── scripts/           operational entry points
├── config/            layered YAML (default/dev/test/prod/local)
├── docs/              see the index below
├── Dockerfile         Streamlit dashboard image
├── Dockerfile.api     FastAPI image
└── render.yaml        Render: careeros-db + careeros-api + careeros-web
```

The packages that carry the workflow:

| Package | Role |
|---|---|
| `careeros-career-brain` | the profile, and the rule that nothing may invent a fact about you |
| `careeros-llm` | the LLM gateway — routing, fallback, health, structured output |
| `careeros-ai` | the low-level `AIClient` seam the gateway is built on |
| `careeros-job-providers` | provider SDK: `JobPosting`, filtering, dedupe, registry |
| `careeros-ats-providers` | 9 hosted ATSes over 120 company boards |
| `careeros-job-discovery` | discover → score → store → emit |
| `careeros-application-engine` | résumé, cover letter, answers, ATS report, reviewer |
| `careeros-browser` | `BrowserSession` (Playwright) + `FakeBrowserSession` |
| `careeros-autopilot` | live-page form detection, field mapping, readiness |
| `careeros-application-runner` | fill, verify, report — `FillReport` |
| `careeros-api` | FastAPI backend |
| `careeros-dashboard` | Streamlit UI |
| `careeros-cli` | the `careeros` console command |
| `careeros-tenancy` / `-auth` / `-credentials` | isolation, login, encrypted vault |

The remaining packages are supporting domain surface — CRM, analytics, interview
prep, freelance, billing, offers, personal brand.

| Doc | Covers |
|---|---|
| `docs/current-state.md` | verified state of the working tree |
| `docs/architecture/overview.md` | package map, principles |
| `docs/llm-providers.md` | routing, fallback, provider states, structured output |
| `docs/job-providers.md` | why ATS discovery is company-scoped, dedupe, adding an ATS |
| `docs/application-engine.md` | fill outcomes, frames, submit safety, radio groups |
| `docs/career-profile.md` | the zero-fabrication rule and how it is enforced |
| `docs/testing.md` | the test levels |
| `docs/troubleshooting.md` | symptom → cause → command |

---

## Running CareerOS locally

One-time setup:

```bash
uv sync
uv run playwright install chromium
```

### The web product (two processes, both needed)

API first:

```bash
CAREEROS_ENV=dev uv run uvicorn careeros_api:app --reload --port 8000
```

Then the Next.js front end in a second terminal, pointed at it:

```bash
cd web && CAREEROS_API_BASE=http://localhost:8000 npm run dev
```

Opens on `http://localhost:3000`. Routes include `/dashboard`, `/opportunities`,
`/career-brain`, `/autopilot`, `/watchlist`, `/review`, `/settings`,
`/freelance`, `/pitch-kit`, `/interview`, `/analytics`.

### The Streamlit dashboard (self-contained, one process)

```bash
CAREEROS_SINGLE_USER=1 uv run streamlit run packages/careeros-dashboard/src/careeros_dashboard/app.py
```

`CAREEROS_SINGLE_USER=1` removes login entirely and uses an unscoped local store
— the personal-install mode. Without it you get the multi-tenant flow (marketing
page → sign up → isolated workspace). No API process is required.

### The CLI (no other process needed)

```bash
uv run careeros brain show
uv run careeros search --keywords "performance marketing,paid media"
uv run careeros generate-package --job-url "https://..."
uv run careeros applications
```

Defaults to `.careeros/data`; override with `--data-dir`.

### The autopilot daemon (real browser, local only)

```bash
uv run python scripts/autopilot_daemon.py --workspace-id <ID> --once --show-browser
```

Without `CAREEROS_DATABASE_URL` it runs against local SQLite, offline. It
prepares applications and stops; it does not submit.

### Checks

```bash
uv run python scripts/e2e_smoke.py --per-ats 3   # full workflow, live boards, never submits
uv run python scripts/verify_ats_boards.py       # are the 120 company boards still alive?
uv run pytest                                    # full suite, ~6 min
uv run pytest -m "not browser"                   # faster; skips real-Chromium tests
```

### Environment variables

| Variable | Effect |
|---|---|
| `CAREEROS_SINGLE_USER=1` | no login, unscoped store (personal install) |
| `CAREEROS_DATA_DIR` | local data dir (default `.careeros/data`) |
| `CAREEROS_DATABASE_URL` | use Postgres instead of local SQLite |
| `CAREEROS_SECRET_KEY` | encrypts stored secrets — see the warning below |
| `CAREEROS_AI_API_KEY` | one AI key; the vendor is inferred from its shape |
| `CAREEROS_AI_MODEL` | model override |
| `CAREEROS_LLM_PRIORITY` | comma-separated provider ids, best first |
| `CAREEROS_LLM_CLI_ENABLED=0` | ignore locally installed agent CLIs (set this on a server) |
| `CAREEROS_ENABLE_LINKEDIN=0` | switch off the browser-reading LinkedIn source |

> **Operational warning.** `CAREEROS_SECRET_KEY` encrypts stored credentials.
> Rotating or losing it makes every previously stored secret undecryptable. Set
> it once per deployment and keep it stable.

---

## LLM authentication

No key is required to run CareerOS. Without one, AI features fall back to their
deterministic equivalents.

**Claude / Gemini / Codex (CLI providers).** Install the CLI and authenticate it
yourself — CareerOS reads the session you already have and never handles your
credentials:

```bash
claude          # then /login
codex login
# Gemini: set GEMINI_API_KEY, or configure ~/.gemini/settings.json
```

**GPT / OpenAI, or any API key.** Set `CAREEROS_AI_API_KEY` in your environment,
or store a key per workspace through Settings → AI, where it is held in the
encrypted credential vault. The vendor is inferred from the key's shape.

Never commit a key. Check what is actually usable with:

```bash
uv run python -c "from careeros_llm import LLMGateway; [print(h.describe()) for h in LLMGateway.from_env().provider_report()]"
```

---

## Testing

```
2,500 passed · 1 skipped · 0 failed
```

Tests run at several levels: unit tests against a `FakeBrowserSession`;
**real-browser tests** against saved ATS-shaped HTML fixtures; integration tests
across provider → normalization → registry; and live smoke tests against real
boards and real forms.

The real-browser and live layers exist because a green unit suite did not catch
several defects that only appear in a real DOM — a radio group text-filled and
raising, `"city"` matching inside `"ethni-city"`, a `<select>` label swallowing
its own options, an anti-bot challenge misreported as a missing form. Each of
those is now a permanent regression test.

**This does not mean every real-world ATS scenario is covered.** Employers change
their forms, and the live tests sample a handful of postings per run.

---

## Current limitations

- **Lever choice/select automation.** Some radio and select groups fail to set on
  live Lever forms. The failure is reported, not hidden.
- **Anti-bot variability.** Workable and SmartRecruiters intermittently serve
  Cloudflare or DataDome challenges, especially after repeated automated visits.
  Detected and reported; not worked around.
- **Employer redirects.** Many Greenhouse customers route applications to their
  own careers site, where there is no hosted form to fill.
- **Workday is discovery-only.** Its forms need an account first.
- **Recruitee, Personio and BambooHR application support is unverified.**
- **Provider authentication.** Gemini and Codex are implemented but unexercised
  here; GPT needs a key. Only Claude has been live-tested.
- **Evidence gaps are the user's to close.** Where a profile lacks evidence for a
  claim, CareerOS withholds it rather than lowering the bar. Resolving that means
  supplying evidence, not changing the validator.
- **Genuine job disqualifications** — a US-only role for a candidate who is not
  US-authorized — are surfaced, not worked around.
- **The ATS keyword report reads only `posting.tags`**, and hosted-ATS postings
  mostly have none, so that report is usually empty on exactly the postings that
  matter.

---

## Safety and application policy

- CareerOS **does not invent answers**.
- Unsupported and disputed professional claims are **blocked** from every
  generated document.
- A question that cannot be answered truthfully becomes **`NEEDS_USER_INPUT`**,
  with the reason and what would resolve it.
- **Job disqualifications are surfaced**, and technical submission readiness
  never overrides one.
- The final submit control is identified **semantically**, and re-verified at the
  moment of the click — a form can re-render between detection and submission.
- **CareerOS stops before final submission. No application is submitted
  automatically.**

---

## Project status

CareerOS can take a real posting from discovery through to a filled, validated
application form and stop at submission-ready for your review. It has been run
end-to-end against live boards and real ATS forms.

It does **not** submit applications. A human reviews and submits.

The most recent work hardened the Career Brain's provenance controls and the
application workflow: unsupported and conflicting claims are now blocked from
generated materials, and technical form readiness was separated from the
recommendation about whether to apply at all. Suite: **2,500 passed, 1 skipped,
0 failed**.
