"""GlassdoorProvider: FIND_JOBS over Glassdoor via an anti-detect browser
reading each search-result card's data-test-anchored fields.

Local-daemon only: needs a real browser and a real IP.

Not part of ``default_provider_registry`` (see
``docs/plans/browser-gated-sources.md``) — register it explicitly wherever
a real browser is actually available:
``registry.register(GlassdoorProvider())``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager

from careeros_browser import BrowserSession, launch_camoufox_session
from careeros_common import get_logger
from careeros_glassdoor_provider.parser import (
    CARD_SELECTOR,
    PROVIDER_ID,
    has_listing_marker,
    make_search_url,
    parse_card,
)
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
)

logger = get_logger(__name__)

DEFAULT_TERM = "jobs"
PAGE_SIZE = 30
DEFAULT_MAX_PAGES = 4

SessionFactory = Callable[[], AbstractContextManager[BrowserSession]]


@contextmanager
def _default_session_factory() -> Iterator[BrowserSession]:
    with launch_camoufox_session() as session:
        yield session


class GlassdoorProvider(JobProvider):
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
        limit: int,
        source_errors: list[str],
    ) -> list[JobPosting]:
        postings: list[JobPosting] = []
        page = 1

        while page <= self._max_pages and len(postings) < limit:
            session.goto(make_search_url(keyword=keyword, page=page))
            body_blocks = session.query_all_html("body")
            body = body_blocks[0] if body_blocks else ""

            if not has_listing_marker(body):
                # The page never rendered a real results page — most
                # likely the bot wall didn't clear. Distinguishable from a
                # genuinely empty result set, which ships the marker too.
                source_errors.append(
                    f"glassdoor: '{keyword}' page {page} — no listing marker in "
                    "the response (bot wall likely unresolved)"
                )
                break

            cards = session.query_all_html(CARD_SELECTOR)
            postings.extend(posting for card in cards if (posting := parse_card(card)))

            if len(cards) < PAGE_SIZE:
                break
            page += 1

        return postings

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        keywords = [k.strip() for k in query.keywords if k.strip()] or [DEFAULT_TERM]

        postings: list[JobPosting] = []
        seen: set[str] = set()
        source_errors: list[str] = []

        with self._session_factory() as session:
            for keyword in keywords:
                for posting in self._search_one_term(
                    session, keyword=keyword, limit=query.limit, source_errors=source_errors
                ):
                    if not posting.external_id or posting.external_id in seen:
                        continue
                    seen.add(posting.external_id)
                    postings.append(posting)
                if len(postings) >= query.limit:
                    break

        return JobSearchResult(postings=postings[: query.limit], source_errors=source_errors)

    def health_check(self) -> ProviderHealth:
        # Optimistic, matching NaukriProvider/GradcrackerProvider/
        # ZipRecruiterProvider: a real check would mean launching a browser
        # on every health probe. search() itself reports a blocked run
        # through source_errors, which is where the real signal belongs.
        return ProviderHealth(status=HealthStatus.HEALTHY)
