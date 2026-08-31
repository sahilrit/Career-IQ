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
