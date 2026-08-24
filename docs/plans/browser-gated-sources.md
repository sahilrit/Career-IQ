# Scope: browser-gated job sources (Naukri, Gradcracker, UK Visa Jobs)

Status: **shared layer + Naukri + Gradcracker shipped. UK Visa Jobs investigated,
not built — see §7.** Written 2026-08-24, updated same day after execution.

These are the JobOps sources CareerOS had not built, because unlike LinkedIn,
Hiring Cafe, Adzuna, Working Nomads and Golang Jobs, they cannot be reached
with a plain HTTP request. They need a real, anti-detect browser. This document
scoped what that takes before any code was written (§1-6 below, unchanged from
the original scoping pass); §7 records what actually happened once it was built.

---

## 1. The decision that dominates everything: where does the browser run?

**The deployed API has no browser, by design.** `Dockerfile.api` builds "no
Streamlit/Playwright/browser" — only the API's dependency subtree — and Render's
free tier could not run a headed browser even if it did. `careeros-browser`
today is vanilla headless Chromium (`launcher.py`), launched only where someone
has run `playwright install chromium` — which in practice is the **local
autopilot daemon**, the one place in CareerOS a real browser runs.

So a browser-gated provider **cannot** be a normal `JobProvider` in the API's
`search_all` registry the way every current source is. There are three homes for
it, and picking one is the first and biggest decision:

| Option | What it means | Cost | Fit |
|---|---|---|---|
| **A. Local daemon only** | Browser discovery runs in the user's own autopilot daemon (already has a browser + a real IP), writes postings to the store; the API just reads them. | Low infra. No new services. | Matches how the autopilot already works. Self-hosted users only; no browser scraping from CareerOS servers. |
| **B. Dedicated worker service** | A new Render/Fly service with a browser image + anti-detect stack, driven by a queue, writing results to Postgres. | High: a second deployable, a browser image (~1GB), a job queue, its own scaling and monitoring. Not free-tier. | Turns browser scraping into a hosted feature — and concentrates all the ToS/IP risk on CareerOS's IP. |
| **C. Third-party actor** | Pay Apify/BrightData to run the scrape (this is what JobOps does for Seek). | Per-run cost; a vendor dependency. | Fastest to ship; offloads the browser + IP problem entirely. |

**Recommendation: Option A for Naukri/Gradcracker, Option C if hosted coverage is
ever required.** Option B is a real second product surface (a browser-worker
platform) and should not be built for three job boards. The synchronous
`search_all` request path also can't absorb a 30–90s browser crawl without a
background model, which Option A sidesteps because the daemon is already async
and long-running.

This is the crux. Everything below assumes **Option A** unless noted.

---

## 2. Shared infrastructure to build (once, before any source)

None of the current providers need this, which is why it was deliberately
deferred. The pure-Python primitives already exist in
`careeros_browser.resilience` (challenge detection, a UA-pinned cookie jar,
retry-with-backoff). What's missing is the actual anti-detect browser and the
glue:

1. **An anti-detect browser launch.** Vanilla Playwright Chromium is trivially
   fingerprinted and will be blocked. Python options, in order of preference:
   - **`camoufox`** (PyPI) — the Python wrapper of the same anti-detect Firefox
     JobOps uses via `camoufox-js`. Playwright-compatible, humanized input,
     GeoIP spoofing, WebRTC block. ~200MB browser binary to bake into the
     daemon's environment.
   - **`patchright`** — a patched, undetected Playwright drop-in. Lighter, but
     less battle-tested than Camoufox for hard Cloudflare.
   - Fallback: `curl_cffi` with browser TLS impersonation for the *HTTP-after-
     solve* calls (Naukri's XHR, once a session cookie exists).
2. **A headed human-solve flow.** When headless can't pass a challenge, open a
   visible browser, let the human solve it, capture `cf_clearance` + the UA that
   earned it (the cookie jar already stores this pair). In the local-daemon model
   this is easy — the user is at the machine. This is the piece that makes hard-
   blocked sources tractable at all.
3. **Wire the primitives together** into a `ResilientBrowserSession` in
   `careeros-browser`: navigate → detect challenge → solve-or-reuse-cookies →
   retry, on top of the Camoufox launch. ~1–2 days once the launch works.

**Effort for the shared layer: ~1 week**, most of it fighting the browser binary
into the daemon environment and proving one Cloudflare solve end-to-end.

---

## 3. Per-source breakdown

### Naukri (India's largest board — highest value here)
- **Mechanism (from the JobOps audit):** drive the real site with an anti-detect
  browser, then **intercept the XHR** to `/jobapi/v3/search` rather than parse
  HTML — the site authenticates its own request, we read the JSON off the wire.
  Paginate by clicking "next" and awaiting each API response.
- **Blocker:** Naukri returns `Access Denied` (Akamai) to anything that isn't a
  convincing browser. Needs the full anti-detect stack.
- **Effort after shared layer:** ~3–4 days (XHR interception, pagination,
  parsing the `jobapi` shape into `JobPosting`, tests against captured payloads).
- **Value:** high — Naukri is the dominant board in India, a market with no good
  coverage in the current provider set.

### Gradcracker (UK STEM graduates)
- **Mechanism:** Cloudflare-protected HTML. JobOps uses Crawlee + Camoufox +
  `impit`. Navigate through category pages, parse listing HTML, follow to detail.
- **Blocker:** Cloudflare managed challenge (the 200-with-challenge-HTML case the
  resilience primitives already detect).
- **Effort after shared layer:** ~3–4 days (route walking + HTML parsing; more
  parsing surface than Naukri, no clean JSON API).
- **Value:** medium, narrow — UK STEM new-grads only.

### UK Visa Jobs (UK visa-sponsorship roles)
- **Mechanism:** **credentialed.** Log in with the *user's own* email/password,
  then hit the internal `/ukvisa-api/api/fetch-jobs-data`. Token refresh needed.
- **Blocker:** it's an authenticated flow, not just anti-detect. Requires storing
  and using the user's UK Visa Jobs credentials (vault), a login automation, and
  token refresh.
- **Effort after shared layer:** ~4–5 days (login flow, credential vault entry,
  token lifecycle, the internal API mapping).
- **Value:** medium, and **note the overlap:** the visa-sponsorship *signal* is
  better served by the separate "visa sponsorship matching" project (ingest the
  UK/NL government sponsor registers — no login, no browser, cleaner data). If
  that ships, UK Visa Jobs as a source is largely redundant.

---

## 4. ToS, IP, and maintenance risk (read before committing)

- **Terms of service.** Naukri, Gradcracker and UK Visa Jobs all prohibit
  automated collection. In the **local-daemon** model the traffic comes from the
  *user's* machine and IP, which is the same posture that makes LinkedIn
  defensible today. In a **hosted worker** model it all comes from CareerOS's IP
  — much higher exposure. This is a strong argument for Option A.
- **Credentials (UK Visa Jobs).** Storing a user's third-party password is a real
  security surface. The vault exists, but this is the one source that adds
  credential-handling risk on top of scraping risk.
- **The anti-detect arms race.** Anti-bot is maintenance-forever, not build-once.
  Camoufox and the challenge markers need updating whenever Cloudflare/Akamai
  change. JobOps carries this cost continuously; so would we. Budget ongoing
  upkeep, not just the build.

---

## 5. Recommended sequencing (if we proceed)

1. **Shared anti-detect layer** in `careeros-browser` (Camoufox launch +
   `ResilientBrowserSession` over the existing primitives + headed solve). ~1 wk.
   Prove it on **one** Cloudflare solve before building any provider.
2. **Naukri** — highest value, cleanest mechanism (JSON via XHR). ~3–4 days.
   This is the source worth doing; if only one gets built, it's this.
3. **Gradcracker** — only if UK-grad coverage is a priority. ~3–4 days.
4. **UK Visa Jobs** — **deprioritise** in favour of the sponsor-register project,
   which delivers the same signal without a login or a browser.

**Total for the sane subset (shared layer + Naukri): ~2 weeks.** The full three-
source set: ~4 weeks plus permanent anti-detect maintenance.

---

## 6. Honest recommendation

The browser-gated sources are **lower ROI than their absence suggests.** One of
them (Naukri) is genuinely valuable; the other two are narrow or redundant. The
work is dominated by a one-time anti-detect infrastructure cost plus permanent
upkeep, and it only fits cleanly in the **local-daemon** model — it does not make
CareerOS's hosted API scrape these sites, and shouldn't.

If the goal is "more real coverage for the most users," **the sponsor-register
visa project and Naukri (local-daemon)** are the two worth doing, in that order.
Building a hosted browser-worker platform for three job boards is not.

---

## 7. What actually got built (2026-08-24)

The shared layer, Naukri and Gradcracker were built same-day, test-first,
local-daemon-only exactly as recommended above. UK Visa Jobs was investigated
and deliberately not built. Details below.

### Shared anti-detect layer — DONE

`careeros_browser.resilience` already had the pure-Python pieces (challenge
detection, UA-pinned cookie jar, retry). Added on top:

- `launch_camoufox_session()` — an anti-detect Firefox launch alongside the
  existing vanilla-Chromium one. Verified against Camoufox's own source (not
  guessed) that it wraps Playwright's context manager and hands back a real
  `Browser`, so `PlaywrightBrowserSession` — built against Playwright's `Page`
  interface — wraps a Camoufox page exactly as it wraps a Chromium one; no new
  session class needed. `camoufox` is an optional dependency; importing
  `careeros_browser` never requires it, only calling the launcher does.
- `BrowserSession.capture_response_after()` — run an action, return the body
  of the first network response matching a URL pattern. This is what makes
  Naukri's XHR-interception approach possible without extending the protocol
  further than one method.
- `BrowserSession.query_all_html()` — outer HTML of matching elements, for
  markup too irregular for `query_all`'s flat sub-selector map (Gradcracker's
  dt/dd label/value pairs).
- `FakeBrowserSession` gained matching test doubles plus `set_click_failure()`
  for simulating "no more pages."

**A real bug was caught before shipping**, not after: the first pagination
draft clicked "Next" *before* starting to listen for the response, which races
real navigation (the request can fire and complete before listening begins).
Caught by writing a parity test asserting the fake and real sessions behave
identically when the action itself fails — the test failed, which is what
surfaced the bug. Fixed in both the provider and the fake.

75 tests (careeros-browser package). No browser binary or camoufox install
required to run them.

### Naukri — DONE

Naukri's `/jobapi/v3/search` returns HTTP 406 "recaptcha required" to a plain
request (verified live). The provider drives Camoufox to the search page and
reads the JSON response via `capture_response_after` rather than scraping
rendered markup. The row shape (`jdURL`, `placeholders[]`, `salaryDetail`,
`tagsAndSkills`, ...) is grounded in a working scraper's verified source, not
guessed. A hidden salary (`salaryDetail.hideSalary=true`) is never surfaced.
A blocked keyword reports itself through `source_errors` rather than silently
contributing nothing. 40 tests.

### Gradcracker — DONE

A plain request returns HTTP 403 (verified live). The provider drives Camoufox
to each role x region search page (Gradcracker has no keyword search — its
taxonomy is role slugs crossed with UK regions) and parses the rendered
`article[wire\:key]` cards via a small stdlib-only HTML-to-tree parser
(`htmltree.py`), needed because the dt/dd label/value structure doesn't fit a
flat sub-selector map. **The card fixture used to test the parser is an
honest reconstruction, not a capture** — Gradcracker is Cloudflare-blocked, so
unlike Naukri's JSON API there was no way to inspect real production HTML from
this environment. It's built from verified Playwright locators in a working
scraper's source, documented as such rather than presented as a real capture.
A run where every combination is blocked reports itself; one blocked
combination among several that work does not (that's an ordinary empty
region, not a sign of being blocked). 38 tests.

### UK Visa Jobs — investigated, not built

Unlike Naukri and Gradcracker, UK Visa Jobs is **not** Cloudflare/anti-bot
gated — a plain request to its internal API returned `{"error": "Invalid
token"}`, a pure auth problem. That should have made it the *easiest* of the
three. It wasn't, because the real login endpoint could not be responsibly
determined from this environment:

- The site is a client-rendered SPA; the login POST target is not present as
  a literal string in its ~2.5MB minified JS bundle (likely built at runtime
  from concatenated route fragments).
- Probing plausible REST paths (`/signin`, `/login`, `/auth/login`, ...)
  found one that returns HTTP 200 for *any* body — but its response turned
  out to be generic CMS page content for the sign-in page, not an
  authentication result. It is not the real login endpoint; it only looks
  like a match by returning 200.
- Guessing further and shipping an integration against an unverified endpoint
  would risk silently-wrong code (or worse, probing behavior indistinguishable
  from credential-stuffing against a real auth endpoint) — the kind of thing
  the security posture in this session's operating rules exists to prevent.

This isn't a capability gap the shared anti-detect layer would fix — no
browser challenge stands in the way, only an SPA whose real API surface needs
a live network inspector to observe. It also confirms §6's original call: UK
Visa Jobs was already the one to deprioritise, and the sponsor-register
project remains the better way to deliver the same visa-sponsorship signal.
