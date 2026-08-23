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

### Week 1 — close the source gap (15 sources vs their 16, no browser scrapers)
- `careeros-jobspy-provider` — in-process `python-jobspy`, exposes LinkedIn + Indeed (+ Glassdoor when upstream recovers).
- `careeros-hiringcafe-provider` — httpx GET + `__NEXT_DATA__` regex.
- Upgrade `careeros-workingnomads-provider` to `/jobsapi/_search` (~40 lines) for ranked results + full descriptions.
- `careeros-adzuna-provider` — free key, multi-country.

### Week 2 — LLM scoring
Keep `careeros_job_discovery.scoring` as the cheap first pass; add an LLM stage for postings
that clear it. Copy the *shape* of their `scorer.ts` prompt — one structured-output call returning:
1. **job fact patches** — corrections to whitelisted scraped fields, each requiring a verbatim
   listing excerpt + confidence (high/medium/low); medium may only fill missing values.
2. **job brief** — seven neutral arrays (`role_summary`, `they_want`, `specifics`,
   `company_offers`, `practical_details`, `missing_or_unclear`, `repeated_signals`).
3. **candidate score** 0–100 + reason.

Wire through `careeros-ai` (bring-your-own-key already exists).

### Week 3 — application reply tracking
`integrations_google.py` already has half the Gmail OAuth. Add: pull last 90 days →
match against open applications → LLM classify → transition stage (Interviewing / Rejected).

### Week 4 — anti-bot layer in `careeros-browser`
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
