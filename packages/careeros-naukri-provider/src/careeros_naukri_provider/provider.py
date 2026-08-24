"""NaukriProvider: FIND_JOBS over Naukri via an anti-detect browser.

Naukri is a client-rendered SPA whose search results come from
``/jobapi/v3/search``, an endpoint that returns HTTP 406 "recaptcha
required" to a plain HTTP request (verified live). This provider instead
drives a real (anti-detect) browser to the search page and reads the
same JSON response the page's own script fetches — via
``BrowserSession.capture_response_after`` — rather than trying to call
the API directly or scrape whatever the script renders from it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager

from careeros_browser import BrowserSession, ResponseTimeoutError, launch_camoufox_session
from careeros_common import get_logger
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
)
from careeros_naukri_provider.parser import (
    PROVIDER_ID,
    is_job_entry,
    make_search_url,
    parse_job_entry,
    parse_search_response,
)

logger = get_logger(__name__)

SEARCH_API_MARKER = "jobapi/v3/search"
DEFAULT_TERM = "jobs"
RESULTS_PER_PAGE = 20
DEFAULT_MAX_PAGES = 3
PAGE_TIMEOUT_MS = 20_000

# Naukri's "Next" control has no stable id; try a few real, valid Playwright
# selectors (:has-text() and attribute-contains are genuine Playwright CSS
# extensions, not guesses) in order, treating the first that clicks as
# correct and any click failure as "no more pages" rather than an error.
_NEXT_PAGE_SELECTORS: tuple[str, ...] = (
    "a:has-text('Next')",
    "button:has-text('Next')",
    "[aria-label*='Next' i]",
)

SessionFactory = Callable[[], AbstractContextManager[BrowserSession]]


@contextmanager
def _default_session_factory() -> Iterator[BrowserSession]:
    with launch_camoufox_session() as session:
        yield session


def _click_next_and_capture(session: BrowserSession, *, timeout_ms: int) -> str | None:
    """Click "Next" and return the following page's API response body, or
    None if no candidate selector both exists and leads to a response.

    The click has to happen *as* the action passed to
    ``capture_response_after`` — clicking first and only then starting to
    listen for the response would race the real navigation, since the
    request can fire and complete before listening ever begins.
    """
    for selector in _NEXT_PAGE_SELECTORS:
        try:
            return session.capture_response_after(
                lambda selector=selector: session.click(selector),
                url_contains=SEARCH_API_MARKER,
                timeout_ms=timeout_ms,
            )
        except ResponseTimeoutError:
            continue
    return None


class NaukriProvider(JobProvider):
    """Local-daemon-only: needs a real browser and a real IP.

    Not part of ``default_provider_registry`` (see
    ``docs/plans/browser-gated-sources.md``) — register it explicitly
    wherever a real browser is actually available:
    ``registry.register(NaukriProvider())``.
    """

    def __init__(
        self,
        *,
        session_factory: SessionFactory | None = None,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> None:
        self._session_factory = session_factory or _default_session_factory
        self._max_pages = max(1, max_pages)

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def _search_one_term(
        self,
        session: BrowserSession,
        *,
        keyword: str,
        location: str | None,
        limit: int,
        source_errors: list[str],
    ) -> list[JobPosting]:
        postings: list[JobPosting] = []
        url = make_search_url(keyword=keyword, location=location)

        try:
            body = session.capture_response_after(
                lambda: session.goto(url),
                url_contains=SEARCH_API_MARKER,
                timeout_ms=PAGE_TIMEOUT_MS,
            )
        except ResponseTimeoutError as exc:
            # The search API never answered — a challenge intercepted the
            # request, or the session has no valid clearance. Report it
            # rather than let this term silently contribute nothing, which
            # would be indistinguishable from "no jobs matched".
            source_errors.append(f"naukri: '{keyword}' — {exc}")
            return postings

        rows = parse_search_response(body)
        postings.extend(parse_job_entry(row) for row in rows if is_job_entry(row))

        page = 1
        while rows and page < self._max_pages and len(postings) < limit:
            body = _click_next_and_capture(session, timeout_ms=PAGE_TIMEOUT_MS)
            if body is None:
                break
            page += 1
            rows = parse_search_response(body)
            postings.extend(parse_job_entry(row) for row in rows if is_job_entry(row))

        return postings

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        keywords = [k.strip() for k in query.keywords if k.strip()] or [DEFAULT_TERM]
        location = next((loc.strip() for loc in query.locations if loc.strip()), None)

        postings: list[JobPosting] = []
        seen: set[str] = set()
        source_errors: list[str] = []

        with self._session_factory() as session:
            for keyword in keywords:
                for posting in self._search_one_term(
                    session,
                    keyword=keyword,
                    location=location,
                    limit=query.limit,
                    source_errors=source_errors,
                ):
                    if posting.external_id in seen:
                        continue
                    seen.add(posting.external_id)
                    postings.append(posting)
                if len(postings) >= query.limit:
                    break

        return JobSearchResult(postings=postings[: query.limit], source_errors=source_errors)

    def health_check(self) -> ProviderHealth:
        # Optimistic, matching GreenhouseProvider: actually launching a
        # browser and running a request here would double the cost of every
        # search, since the registry health-checks every provider before
        # every search. search() itself reports a blocked run through
        # source_errors, which is where the real signal belongs.
        return ProviderHealth(status=HealthStatus.HEALTHY)
