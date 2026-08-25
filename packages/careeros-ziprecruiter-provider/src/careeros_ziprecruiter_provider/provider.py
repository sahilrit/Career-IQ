"""ZipRecruiterProvider: FIND_JOBS over ZipRecruiter via an anti-detect
browser reading the search page's embedded JSON-LD listing data.

Local-daemon only: needs a real browser and a real IP.

Not part of ``default_provider_registry`` (see
``docs/plans/browser-gated-sources.md``) — register it explicitly wherever
a real browser is actually available:
``registry.register(ZipRecruiterProvider())``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager

from careeros_browser import BrowserSession, launch_camoufox_session
from careeros_common import get_logger
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
)
from careeros_ziprecruiter_provider.parser import (
    PROVIDER_ID,
    extract_ld_json_items,
    has_ld_json_block,
    is_job_entry,
    make_search_url,
    parse_job_entry,
)

logger = get_logger(__name__)

DEFAULT_TERM = "jobs"
PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 4
PAGE_LOAD_WAIT_MS = 6_000

SessionFactory = Callable[[], AbstractContextManager[BrowserSession]]


@contextmanager
def _default_session_factory() -> Iterator[BrowserSession]:
    with launch_camoufox_session() as session:
        yield session


class ZipRecruiterProvider(JobProvider):
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

    def _fetch_page_html(self, session: BrowserSession, url: str) -> str:
        session.goto(url)
        blocks = session.query_all_html("body")
        return blocks[0] if blocks else ""

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
        page = 1

        while page <= self._max_pages and len(postings) < limit:
            url = make_search_url(keyword=keyword, location=location, page=page)
            html = self._fetch_page_html(session, url)

            if not has_ld_json_block(html):
                # The page never rendered real results — most likely the
                # Cloudflare challenge didn't resolve. Distinguishable from
                # a genuinely empty result set, which does ship the block.
                source_errors.append(
                    f"ziprecruiter: '{keyword}' page {page} — no listing data in "
                    "the response (challenge likely unresolved)"
                )
                break

            items = extract_ld_json_items(html)
            usable = [item for item in items if is_job_entry(item)]
            postings.extend(parse_job_entry(item) for item in usable)

            if len(items) < PAGE_SIZE:
                break
            page += 1

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
                    if not posting.external_id or posting.external_id in seen:
                        continue
                    seen.add(posting.external_id)
                    postings.append(posting)
                if len(postings) >= query.limit:
                    break

        return JobSearchResult(postings=postings[: query.limit], source_errors=source_errors)

    def health_check(self) -> ProviderHealth:
        # Optimistic, matching NaukriProvider/GradcrackerProvider: a real
        # check would mean launching a browser on every health probe, which
        # the registry runs before every search. search() itself reports a
        # blocked run through source_errors, which is where the real signal
        # belongs.
        return ProviderHealth(status=HealthStatus.HEALTHY)
