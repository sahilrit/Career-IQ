# Competitive integration log

What was studied in three external projects, what was adopted, what was
rejected, and why. Kept so we do not re-litigate these decisions later.

## Licences — the constraint that shaped everything

| Project | Licence | What that allows |
|---|---|---|
| [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search) | MIT | code and ideas, with attribution |
| [santifer/career-ops](https://github.com/santifer/career-ops) | MIT | code and ideas, with attribution |
| [feder-cr/Jobs_Applier_AI_Agent_AIHawk](https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk) | **AGPL-3.0** | **ideas only** |

AIHawk is AGPL-3.0. Copying its code into CareerOS, which is a hosted
multi-tenant product, would put CareerOS under AGPL. Nothing was copied from it.

## Corrections to the brief's premises

The brief was written from READMEs. Reading the source changed three things:

**career-ops has no Playwright ATS form filling.** The brief expected it to be
the source of "automatic form filling". It is not: `browser-extract.mjs` states
it is "STRICTLY READ-ONLY: no clicks, typing, or form fills — that boundary is
exactly what keeps this separate from `apply`". Its only Playwright writes are
one German job-board search (`scan-interamt.mjs`) and PDF rendering. Its `apply`
prepares materials for a human.

**ai-job-search has no form filling either**, and is Denmark/Canada-focused
(jobnet, jobindex, jobdanmark, jobbank) plus LinkedIn. It is a set of Claude
Code skills — markdown prompts — not an application runtime.

**So no external project could supply the form-filling engine.** CareerOS's own
browser layer was the only implementation, which reframed the work: rather than
adopting a better engine, the job was making the existing one *honest* about
what it had actually done. That is where `FillReport` came from.

**career-ops has 92 providers, not 81** — and they are company-board scoped
(`portals.yml` names companies), not global search. That is not a limitation of
their design; it is a fact about hosted ATSes, which have no global search API.
Adopting that model is the single most valuable thing taken from any of the
three.

---

## career-ops → careeros-ats-providers

**Adopted (ported to Python; the projects share no runtime — career-ops is ESM
JavaScript, CareerOS is Python, so this is reimplementation from a read of the
source, not a copy):**

- The **company-board-scoped discovery model**. Discovery names companies and
  crawls their boards. This is now `boards.py` and the reason ATS coverage went
  from 3 sources to 9.
- The **thin adapter contract**: an adapter knows its hosts, how to build URLs,
  and how to map one posting. Concurrency, error isolation and health are
  written once. Adding an ATS is one file.
- **Host allowlisting with redirects refused.** Adapters derive URLs from
  config, so the final URL — after query parameters — is checked against an
  explicit host set, and a redirect is an error rather than something to follow.
- Four **field-level facts learned from their bug history**, each now with a
  test naming the failure:
  - Greenhouse boards that hide the city behind a work-model string ("Hybrid")
    and keep it in `/offices`
  - Greenhouse bodies arriving **double-encoded**, so entities must be decoded
    before tags are stripped
  - Lever timestamps in epoch **milliseconds**
  - Ashby compensation quoted **per interval**, needing annualization

**Rejected:**

- Their tracker, LaTeX CV pipeline, and dashboard. CareerOS has its own, and the
  brief is explicit that this is not a merge of four applications.
- Their single-user file-on-disk storage. CareerOS is multi-tenant.
- `portals.yml` as a config format. The same model is expressed in Python so it
  is type-checked and testable.

## ai-job-search → the reviewer and question handling

**Adopted (as architecture and prompt design, not code — theirs is markdown
skills):**

- The **drafter → reviewer** split, with the reviewer told to find problems and
  explicitly not to approve. `careeros_application_engine.review`.
- Their **grounding rule** — every claim must be defensible from the profile —
  turned from a prompt instruction into **deterministic checks**. This is where
  CareerOS goes further: employers, figures and degrees in a draft are checked
  back against the Career Brain in code, so fabrication detection does not
  depend on a model being honest about another model.
- Their **field-type taxonomy** for application questions (deterministic /
  derived / job-specific / subjective / unknown), and the rule that an unknown
  question stops and asks rather than being answered.

**Rejected:**

- Their Danish and Canadian job-board CLIs. Wrong geography for this user.
- Claude Code as the execution environment. CareerOS is a service; it uses the
  `claude` CLI as *one provider behind the gateway*, which is the useful half of
  that idea without the dependency.
- Their PDF visual-inspection step. Real, but it needs a vision model, and the
  ATS text-layer check that matters is already covered by `ats_keyword_coverage`.

## AIHawk → patterns only

**Adopted as ideas (nothing copied — AGPL):**

- That fully autonomous submission is where these systems break, both
  technically and in terms of ToS. CareerOS keeps a human before Submit, and
  `submit()` refuses a form it knows is incomplete.
- That silent per-field failure is the dominant failure mode of a form filler.
  This directly motivated read-back verification.

**Rejected:**

- Its browser automation code and architecture (licence).
- Reintroducing unconstrained auto-submission.

---

## What CareerOS kept that none of them have

Multi-tenancy; employment **and** freelance in one system; the opportunity CRM;
the credential vault; and a genuinely provider-agnostic LLM layer — career-ops
and ai-job-search both bind to a specific AI CLI.

## Tests added

| Area | Tests |
|---|---|
| LLM gateway + CLI providers | 35 |
| ATS adapters, normalization, SSRF guard, provider | 59 |
| Fill verification | 45 |
| Reviewer | 33 |
| Real-browser form fixtures | 12 |
| AI resolution fallback | 8 |

## Known limitations

- **Workday** needs tenant + regional host + site name per company; there is no
  index of them, so each board is added by hand. Eight are configured.
- **BambooHR, Personio, Recruitee** have few configured boards — they are
  small-company ATSes with no public directory of tenants.
- Some employers publish through an ATS but **redirect applications to their own
  careers site** (Stripe, Airbnb, Databricks). There is no hosted form to fill;
  the runner reports this rather than failing obscurely.
- Agent-CLI providers are **slow to start** (seconds), so they are a poor fit
  for request-scoped calls on a hosted server. `CAREEROS_LLM_CLI_ENABLED=0`
  turns them off there.
- The AI reviewer needs a working provider. Without one, the deterministic
  checks still run and the review is marked `ai_reviewed=False`.
