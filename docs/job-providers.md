# Job providers

Two kinds of source, with different shapes and different value.

## Aggregators

RemoteOK, Arbeitnow, Himalayas, Jobicy, WorkingNomads, WeWorkRemotely, TheMuse,
HiringCafe, Adzuna, GolangJobs, Seek, LinkedIn. One provider per site, each
answering a keyword search.

## Hosted ATS boards — `careeros-ats-providers`

Nine ATSes behind one engine: **greenhouse, lever, ashby, smartrecruiters,
workable, recruitee, personio, bamboohr, workday**.

These matter more than the aggregators for one reason: their postings link to
application forms with no login wall and no captcha, so they are the only
sources the application engine can realistically fill end to end.

### Discovery is company-scoped, and that is structural

Hosted ATSes have **no global search API**. Greenhouse cannot tell you "every
Greenhouse job matching growth marketer". You crawl boards you have named. That
is why `boards.py` is a list of companies rather than a clever search
abstraction.

Every slug in it was verified live. Run the checker after editing:

```bash
uv run python scripts/verify_ats_boards.py            # all
uv run python scripts/verify_ats_boards.py greenhouse # one
```

A slug that no longer resolves should be **removed**, not left hopefully: a
dead board costs a request on every search and shows up as a permanent error.

Watch for `(empty)` in that report. SmartRecruiters and Workable answer **200
with an empty board** for a company that does not exist, so a wrong slug is
indistinguishable from a real but empty board by status code alone.

### Adding an ATS

One file in `adapters/`, implementing `AtsAdapter`:

- `allowed_hosts` — the exact hosts it may fetch. Enforced on the final URL,
  after query parameters, and redirects are refused rather than followed.
  Adapters derive URLs from config, so this is the SSRF boundary.
- `fetch_board(entry, http)` — raw postings for one company.
- `to_posting(raw, entry)` — one `JobPosting`, or `None` to skip. Return `None`
  when there is no usable URL: a posting CareerOS cannot open is worse than no
  posting, because it looks actionable in the UI.
- `probe_board(entry, http)` — optional, and worth overriding whenever the
  normal fetch is expensive. Greenhouse's probe fetching the full Stripe board
  *with bodies* blew the registry's 15s health budget and silently dropped the
  largest ATS out of every search.

Concurrency, error isolation, health and filtering are written once in
`AtsBoardProvider`.

### One dead board vs an outage

A board that 404s is skipped and reported in `source_errors`. If **every** board
fails, the provider raises — because returning `[]` there is indistinguishable
upstream from "this ATS had no matching jobs".

### Keyword relevance

Matching a keyword anywhere in a full job description is far too loose. Measured
against 2,170 live Lever postings, a marketing keyword set matched 987 of them —
including "Liquor Store Associate", whose body says "performance" once in
boilerplate.

The rule (`keyword_matches_posting`): **title and tags are the primary signal**.
A description hit counts only for **multi-word** keywords, where a phrase like
"performance marketing" really is about the role. Same query, 104 postings, all
genuinely relevant.

### Employers who do not host a form

Greenhouse's `absolute_url` is whatever the board points at, and for large
customers that is their own careers site. `apply_url` is therefore the canonical
`job-boards.greenhouse.io/{slug}/jobs/{id}`, which is where Figma and Reddit
actually serve the form. Employers who self-host (Stripe, Airbnb, Databricks)
redirect away from it, and the runner reports that as
"redirects to its own careers site" rather than "no form found" — which reads as
a CareerOS bug when it is a fact about the employer.

### Discovery support and application support are different questions

"Nine hosted ATSes" is technically true and practically misleading: an ATS
whose jobs CareerOS can read but whose forms it cannot fill is not the same
product feature as one where an application reaches submission-ready. Both
axes are reported separately (`careeros_ats_providers.capability_table()`):

```
PROVIDER         DISCOVERY  APPLICATION
ashby            SUPPORTED  AUTOMATED
greenhouse       SUPPORTED  PARTIAL
smartrecruiters  SUPPORTED  PARTIAL
workday          SUPPORTED  DISCOVERY_ONLY
recruitee        SUPPORTED  UNVERIFIED
```

`UNVERIFIED` never counts as working: an integration nobody has run against a
live form is a claim, not a capability. Any state other than `AUTOMATED` must
carry a reason, enforced in `AtsCapability.__post_init__` — a limitation with
no reason cannot be planned around. `application_ready_count()` is the number
to quote instead of the adapter count.

### Adding a Workday tenant without a code change

Workday has no global index: every customer is a separate tenant with its own
regional host and site name, so each board is added deliberately. That is
architecture, not a gap — but it must not require an edit to a Python file:

```bash
export CAREEROS_WORKDAY_BOARDS='[
  {"slug": "acme", "name": "Acme", "region": "wd3", "site": "External_Career_Site"}
]'
```

Entries are validated at load time, not at crawl time. A missing `site` or a
region that is not `wd<N>` raises `WorkdayConfigError` naming the problem —
rather than surfacing as a 404 four minutes into a search, which reads like the
company deleted its board. A bad entry raises rather than being skipped:
silently dropping a tenant the user deliberately configured is worse than
refusing to start.

### Deduplication

Two different duplicates exist, and only one of them used to be handled:

1. **Within a provider** — the same posting returned twice.
   `(source_provider, external_id)` catches these exactly.
2. **Across providers** — the same job reached from an aggregator AND from the
   ATS hosting it. These share no ids (Himalayas says `h-8891`, Greenhouse says
   `4001209002`), so the key above never matched them and the user saw the role
   twice. **This is the duplicate that actually shows up in daily use.**

The cross-provider pass is deliberately conservative, because a wrong merge
silently HIDES a real job — worse than showing one twice. Identical apply URL
(ignoring tracking parameters) merges unconditionally; otherwise company, title
and location must all be present and match, so a partial key never collapses
unrelated rows. When two merge, the more useful copy survives: the ATS-hosted
one (it can actually be applied to), then whichever carries a description.
