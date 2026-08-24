# JobOps parity plan

Technical reference distilled from a line-level audit of
[`DaKheera47/job-ops`](https://github.com/DaKheera47/job-ops) (commit `8b6f6ce`, v0.11.0,
3.8k★, AGPLv3 + Commons Clause) on **2026-08-24**.

Full narrative report (artifact): https://claude.ai/code/artifact/86df26fe-8fb0-4d6f-b93b-fff27183887b

**Licensing conclusion:** JobOps carries a Commons Clause on top of AGPLv3 — it may not be
used to provide a paid product or hosted service whose value derives substantially from it.
CareerOS is a paid multi-tenant SaaS, so **we cannot vendor, fork or embed their code**.
Techniques and HTTP endpoints are not copyrightable; reimplement in Python instead.

---

## 1. The five extraction techniques (in cost order)

### T1 — Mobile app private API  → Indeed
Static API key compiled into Indeed's iOS app. No browser, no login, no Cloudflare.
Verified live 2026-08-24 (returned full job HTML).

```
POST https://apis.indeed.com/graphql
Host: apis.indeed.com
content-type: application/json
indeed-api-key: 161092c2017b5bbab13edb12461a62d5a833871e7cad6d9d475304573de67ac8
indeed-locale: en-US
indeed-co: <ISO2 country>
user-agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) … Indeed App 193.1
indeed-app-info: appv=193.1; appid=com.indeed.jobsearch; osv=16.6.1; os=ios; dtype=phone

body: {"query": "query { jobSearch(what: \"...\", limit: N) { results { job { key title description { html } employer { name } } } } }"}
```

### T2 — Logged-out guest endpoint  → LinkedIn
The public infinite-scroll endpoint. Returns raw HTML job cards, no auth.
Verified live: HTTP 200, 28.5 KB, 50 `base-search-card` per call.

```
GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
    ?keywords=<kw>&location=<loc>&start=<0,25,50…>&f_TPR=r<seconds_old>
user-agent: Mozilla/5.0 (Macintosh; …) Chrome/120.0.0.0 Safari/537.36
```
Descriptions: `GET https://www.linkedin.com/jobs/view/{job_id}` (also public).

### T3 — Exposed internal search backend
| Site | Endpoint | Notes |
|---|---|---|
| Working Nomads | `POST /jobsapi/_search` | Raw Elasticsearch DSL. Verified: 1,070 hits, ~8 KB descriptions. **We currently use the weaker `/api/exposed_jobs/` feed.** |
| Golang Jobs | `mvjyjzestmcxxmmmakec.supabase.co` | Supabase anon key shipped to the browser |
| Naukri | `GET /jobapi/v3/search?pageNo=N` | Needs browser bootstrap; see T5 |
| UK Visa Jobs | `/ukvisa-api/api/fetch-jobs-data` | Requires account credentials |
| FreeHire | `/api/v1/agent/jobs/search` | Open |

Working Nomads request body shape:
```json
{"size": 50, "min_score": 2,
 "query": {"bool": {"must": [{"query_string": {"query": "<kw>",
   "fields": ["title^2", "description", "company"]}}],
   "filter": [{"terms": {"locations": ["..."]}}]}}}
```

### T4 — SSR payload harvesting  → Hiring Cafe
Next.js app; search state goes in the query string, results come back embedded.
`GET https://hiring.cafe/?searchState=<url-encoded JSON>&page=N` → regex
`<script id="__NEXT_DATA__">…</script>` out of the HTML. Verified: 991 KB payload,
no Cloudflare challenge. Note the domain now 308-redirects to `hiringcafe.com` — follow redirects.

Generalises to any Next.js / Nuxt / Remix job board (`__NEXT_DATA__`, `__NUXT_DATA__`, RSC flight payloads).

### T5 — Anti-detect browser with human fallback
~700 LOC in `extractors/browser-utils/`. The parts worth reimplementing:

- **Camoufox** (`camoufox-js`, MPL-2.0) instead of vanilla Playwright Firefox:
  `humanize: true, geoip: true, block_webrtc: true`. **Do not block images** — Cloudflare
  checks whether the browser loaded them.
- **Challenge detection by page content, not status code** — CF managed challenges return HTTP 200.
  Markers: `cf-challenge-running`, `cf-turnstile`, `Checking your browser`,
  `challenges.cloudflare.com`, `Just a moment...`, `cf-please-wait`, `cf_chl_opt`.
- **Human-in-the-loop solve**: extractor returns `challengeRequired: <url>`, the pipeline *pauses*,
  a headed Firefox opens inside the container on Xvfb → x11vnc → noVNC.
- **Clearance cookie reuse with UA pinning**: persist `cf_clearance`, `__cf_bm`, `cf_chl_2`,
  `cf_chl_prog`, `__cflb` **together with the exact user-agent that earned them** — CF binds the
  cookie to UA + TLS fingerprint. Reload both for headless runs; share the jar with plain HTTP clients.
- **TLS fingerprint spoofing**: JobSpy uses `tls_client(random_tls_extension_order=True)`.
  Python equivalent for us: `curl_cffi` with browser impersonation.
- **XHR interception** (Naukri): drive the real UI with Camoufox and `waitForResponse` on the
  internal API rather than parsing HTML. The site authenticates itself; we read the wire.

### T6 — Buy it
Seek (AU/NZ) via a paid Apify actor; Adzuna via its official API key. 2 of 16 sources.

---

## 2. Live test results (2026-08-24, no proxy)

| Target | Method | Result |
|---|---|---|
| Indeed | jobspy + raw curl | ✅ full descriptions |
| LinkedIn | jobspy + raw curl | ✅ 50 cards/call, full descriptions |
| Working Nomads | exposed ES | ✅ 1,070 hits |
| Greenhouse | `boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true` | ✅ 578 jobs |
| Hiring Cafe | SSR | ✅ 991 KB |
| Glassdoor | jobspy Apollo GraphQL | ❌ HTTP 400 "location not parsed" (also with city fallback) |
| ZipRecruiter | jobspy | ❌ HTTP 403 |

**Key finding:** LinkedIn/Indeed/Glassdoor in JobOps are a thin wrapper around
[`python-jobspy`](https://github.com/cullenwatson/JobSpy) (**MIT**, 4.1k★), shelled out as a
Python subprocess. Last commit 2026-02-18 — six months stale, which is why Glassdoor and
ZipRecruiter are down. Their scraping moat is one unmaintained MIT dependency plus ~700 LOC
of browser infrastructure. We are already Python, so we can `pip install python-jobspy` and
wrap it **in-process** — strictly simpler than their subprocess + CSV round-trip.

---

## 3. Implementation plan

> **Progress log — 2026-08-24.** Items marked DONE are built, unit-tested,
> linted and live-verified against the real services. Workspace test count:
> 1,635 -> 1,897.

### Deviations from the original plan, and why

**We did not wrap `python-jobspy`.** The audit's own headline finding was that
JobOps' scraping edge is one unmaintained dependency they do not control.
Wrapping it inherits exactly that, plus a compatibility risk against our pinned
`pandas==3.0.5`. Both endpoints were verified by hand during the audit, so
LinkedIn is implemented natively in ~450 lines of httpx plus a stdlib
`html.parser` walk: no new third-party dependency, no subprocess, no CSV
round-trip, and we own the failure mode.

**Indeed is not built.** Its mobile GraphQL API is gated behind a static key
extracted from Indeed's iOS app. Calling it means presenting Indeed's own app
credentials to obtain access they have not granted third parties — a different
act from reading LinkedIn's unauthenticated public endpoint, and one that would
ship inside a publicly distributed product. `careeros-adzuna-provider` covers
comparable volume legitimately. If a key we are entitled to use appears (Indeed
Publisher/Partner), the provider drops into the same interface.

### Week 1 — close the source gap

- **DONE `careeros-linkedin-provider`** — native, no jobspy. Guest search
  endpoint paged 25 at a time, stops on an empty page, 1 req/sec throttle,
  description fetches capped at 40 per search
  (`CAREEROS_LINKEDIN_FETCH_DESCRIPTIONS=0` disables them). Registered by
  default; `CAREEROS_ENABLE_LINKEDIN=0` switches the provider off. 27 tests.
  Live-verified: 5/5 real postings, descriptions 1.7k-12k chars.
- **DONE `careeros-hiringcafe-provider`** — SSR `__NEXT_DATA__` harvesting,
  follows the `hiring.cafe` -> `hiringcafe.com` 308. Cloudflare challenges are
  detected by content marker and raised as a distinct `HiringCafeChallengeError`
  so "blocked" stays distinguishable from "broken". Descriptions are composed
  from Hiring Cafe's own structured extraction (requirements, activities, tools)
  rather than costing a second request per job. 27 tests. Live-verified: 6/6
  postings with descriptions and publish dates.
- **DONE Working Nomads upgraded** to `/jobsapi/_search`. The old
  `/api/exposed_jobs/` feed had no salary, no publish date and no relevance
  ranking — we pulled the whole catalogue and filtered locally. Now split into
  client/parser/provider with salary, publish date, employment type, tags and
  experience level. 15 tests. Live-verified: salary on 4/5, dates on 5/5.
- **DONE `careeros-adzuna-provider`** — official API, free developer key,
  20+ countries. Country is part of Adzuna's URL path rather than a filter, so
  the provider infers it from the requested location (countries checked before
  cities, so "Birmingham, United States" doesn't resolve to GB). Adzuna fills in
  an *estimated* salary when the advert states none and flags it with
  `salary_is_predicted`; we drop those rather than let a guess satisfy a
  candidate's minimum-salary filter. Without `ADZUNA_APP_ID`/`ADZUNA_APP_KEY`
  the provider reports itself DOWN with a registration link instead of failing
  every search. 27 tests.

### Shared-layer fixes found while doing the above

- **DONE `filter_postings(..., applied_server_side={...})`.** LinkedIn, Hiring
  Cafe and Working Nomads all match keywords against full job text at the
  source. Our local haystack is only the fields we parsed — and for LinkedIn,
  descriptions are not even fetched at filter time. Re-applying the keyword
  filter silently discarded most real matches. Providers now declare which
  filters the source already honoured; everything else (salary floor,
  employment type, remote) is still enforced locally. Caught by a test, not in
  production.
- **DONE cheap health checks.** `registry.search_all()` health-checks every
  provider before every search, and the reference implementation answered by
  fetching the entire feed. The new providers answer with a single-document
  request instead.
- **DONE failing sources are reported, never hidden.** `search_all` used to
  swallow a provider exception into an empty list, so a rate-limited or blocked
  source just quietly shrank the result count. `JobSearchResult.source_errors`
  now carries one entry per provider that failed, timed out or was down, and it
  travels all the way to the UI: `DiscoveryRun` -> `CycleSummary` ->
  `SearchResponse.source_errors` -> an amber notice on the search form. The
  Streamlit dashboard, CLI (`careeros search`) and autopilot report the same.
- **DONE per-provider timeouts.** `JobProviderRegistry(search_timeout_seconds=,
  health_timeout_seconds=)`, defaulting to 120s and 15s. The first attempt only
  bounded result *collection*: exiting a `ThreadPoolExecutor` context manager
  joins every worker, so a hung provider put its full duration straight back
  into the caller's wall-clock. A timing test caught it; the pool is now
  released with `shutdown(wait=False, cancel_futures=True)`. That test dropped
  from 30.2s to 0.3s.

### Free for all

- **DONE `careeros_billing.open_access`.** `CAREEROS_OPEN_ACCESS` defaults on;
  every gate resolves through `effective_tier()`, so every workspace is treated
  as Agency. Subscriptions, Stripe webhooks and plan records keep working
  untouched — they just stop deciding anything, and `CAREEROS_OPEN_ACCESS=0`
  restores tier enforcement. `/billing` reports `open_access` and suppresses
  every checkout link; the billing page and the landing pricing section show
  what is included instead of what it costs. 18 new tests.

### Week 2 — LLM scoring — DONE

`careeros_job_discovery.llm_scoring`. The heuristic scorer stays the cheap first
pass; the LLM stage runs on what clears it and does three jobs in one structured
call: propose fact corrections, write a neutral brief, score the candidate
0-100. Almost nothing is trusted — every correction needs a verbatim excerpt
that is then checked against the posting, so a hallucinated quote is dropped;
low confidence dropped, medium may only fill a missing value. The patch
whitelist excludes url/external_id/source_provider. A new salary takes its
currency from the excerpt (a bug found reading real output: the default turned a
GBP advert into USD). Wired through `search_for_jobs` to `/opportunities/search`,
active only when the workspace has an AI key; failures fall back to the
heuristic. 49 tests.

### (original) Week 2 — LLM scoring
Keep `careeros_job_discovery.scoring` as the cheap first pass; add an LLM stage for postings
that clear it. Copy the *shape* of their `scorer.ts` prompt — one structured-output call returning:
1. **job fact patches** — corrections to whitelisted scraped fields, each requiring a verbatim
   listing excerpt + confidence (high/medium/low); medium may only fill missing values.
2. **job brief** — seven neutral arrays (`role_summary`, `they_want`, `specifics`,
   `company_offers`, `practical_details`, `missing_or_unclear`, `repeated_signals`).
3. **candidate score** 0–100 + reason.

Wire through `careeros-ai` (bring-your-own-key already exists).

### Week 3 — application reply tracking — DONE

`careeros-reply-tracking` (new package) + `gmail_reply_sync` in the API. A
deterministic, conservative classifier reads recruiter email; the sync loop
matches by company and advances the application, walking the real transition
graph (APPLIED -> IN_REVIEW -> INTERVIEWING) rather than forcing a jump, and
refusing illegal moves (a rejection on an accepted offer). Idempotent via a
seen-message ledger. Mailbox is a protocol, tested against fixtures; the API
supplies a Gmail-backed implementation over a new gmail.readonly scope and a
"Check inbox for replies" button on the Google settings card. 40 tests.

### (original) Week 3 — application reply tracking
`integrations_google.py` already has half the Gmail OAuth. Add: pull last 90 days →
match against open applications → LLM classify → transition stage (Interviewing / Rejected).

### Week 4 — anti-bot layer — DONE (primitives only, deliberately)

`careeros_browser.resilience`. Built the pure-Python, testable core:
Cloudflare challenge detection (content markers + 403/503-from-CF status), a
persistent cookie jar storing `cf_clearance` with the UA that earned it, and
retry-with-backoff. 54 tests, no browser binary.

**Deliberately did not build** the Camoufox binary, headed human-solve/VNC flow,
Docker changes, or TLS-fingerprint spoofing. Every current provider reaches its
source over plain HTTP — that machinery would be untested, unused infrastructure.
It becomes worthwhile only when a hard-blocked provider (Naukri, Gradcracker, UK
Visa Jobs) is actually added; the primitives above are the core it will build on.

### Also done, beyond the original plan
- **Typeset PDF export** (`careeros_api.resume_pdf`) — replaced the flat latin-1
  text dump with a structured one-column CV rendered from the résumé Markdown;
  transliterates non-latin text instead of dropping it; € / ₹ degrade to EUR / Rs.
  Fixed a real bug: € is cp1252, not latin-1, so the old exporter silently ate it.
- **Company watchlist** (`careeros-watchlist`) — monitor Greenhouse / Lever /
  Ashby boards, diff for new roles, silent first-run baseline, empty-board-is-error
  guard. Lever + Ashby are boards JobOps' watchlist can't reach.

### (original) Week 4 — anti-bot layer in `careeros-browser`
Camoufox launch options, content-marker challenge detection, cookie+UA persistence,
`curl_cffi` TLS impersonation. Add `challenge_required: str | None` to `JobSearchResult`.

**Also fix two registry weaknesses found during this audit:**
- `JobProviderRegistry._search_one` swallows exceptions into `[]` — the user never learns a
  source broke. JobOps returns partial results plus a `sourceErrors` list. Add the same.
- No per-provider timeout. JobOps caps each source at 10 minutes with
  `DISCOVERY_CONCURRENCY = 3`. A hung provider currently stalls our whole `search_all`.

### Weeks 5–6 — beat them where they're weak
- **Watchlist**: we ship Greenhouse + Lever + Ashby; they lack Lever and Ashby. Add seen-job diffing.
- **PDFs**: swap fpdf2 for Typst. Theirs looks designed (Typst + Tectonic + Reactive Resume); ours doesn't.
- **Multi-tenancy**: ours is native, theirs is a retrofit (usage counters/reservations grafted
  onto a single-user SQLite schema). Durable advantage — lean on it.
- **Post-application surface**: interview prep, offer negotiation, freelance, personal brand.
  JobOps stops at "you applied".

---

## 4. Risk to decide deliberately

LinkedIn's and Indeed's ToS prohibit automated collection. JobOps sidesteps the exposure by
being self-hosted — scraping runs from the user's own machine and IP. If CareerOS scrapes these
from Render on behalf of paying customers, the traffic, rate limits and liability concentrate on us.

**Mitigation is architectural:** make aggressive providers opt-in and user-credentialed (user's
own key/proxy where possible) and keep polite public-API providers as the default path.
