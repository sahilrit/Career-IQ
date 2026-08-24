"""GradcrackerProvider: FIND_JOBS over Gradcracker via an anti-detect
browser.

Gradcracker is Cloudflare-protected — a plain HTTP request returns 403
(verified live). This drives a real (anti-detect) browser to each
role/region search page, waits for the job cards to render, and reads
their outer HTML for a pure parser to extract.

Gradcracker has no keyword search in the JobOps sense — its taxonomy is
role slugs (``web-development``, ``software-systems``, ...) crossed with
UK regions, so a full search iterates every role x region combination
rather than issuing one query per keyword.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager

from careeros_browser import BrowserSession, SelectorTimeoutError, launch_camoufox_session
from careeros_common import get_logger
from careeros_gradcracker_provider.parser import (
    CARD_SELECTOR,
    PROVIDER_ID,
    make_search_url,
    parse_article,
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

# JobOps' own defaults for this exact board, kept as ours: a small role set
# and the UK's standard regional split.
DEFAULT_ROLES: tuple[str, ...] = ("web-development", "software-systems")
DEFAULT_REGIONS: tuple[str, ...] = (
    "london-and-south-east",
    "north-west",
    "yorkshire",
    "east-midlands",
    "west-midlands",
    "south-west",
)

CARD_WAIT_TIMEOUT_MS = 10_000

SessionFactory = Callable[[], AbstractContextManager[BrowserSession]]


@contextmanager
def _default_session_factory() -> Iterator[BrowserSession]:
    with launch_camoufox_session() as session:
        yield session


class GradcrackerProvider(JobProvider):
    """Local-daemon-only: needs a real browser and a real IP.

    Not part of ``default_provider_registry`` (see
    ``docs/plans/browser-gated-sources.md``) — register it explicitly
    wherever a real browser is actually available:
    ``registry.register(GradcrackerProvider())``.
    """

    def __init__(
        self,
        *,
        session_factory: SessionFactory | None = None,
        roles: tuple[str, ...] = DEFAULT_ROLES,
        regions: tuple[str, ...] = DEFAULT_REGIONS,
    ) -> None:
        self._session_factory = session_factory or _default_session_factory
        self._default_roles = roles
        self._regions = regions

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        roles = [k.strip() for k in query.keywords if k.strip()] or list(self._default_roles)

        postings: list[JobPosting] = []
        seen: set[str] = set()
        combos_tried = 0
        combos_blocked = 0

        with self._session_factory() as session:
            for region in self._regions:
                for role in roles:
                    combos_tried += 1
                    url = make_search_url(role=role, region=region)
                    session.goto(url)
                    try:
                        session.wait_for_selector(CARD_SELECTOR, timeout_ms=CARD_WAIT_TIMEOUT_MS)
                    except SelectorTimeoutError:
                        # No cards ever rendered. Usually a genuinely empty
                        # role/region combination; only worth reporting if
                        # it turns out *every* combination did this (see
                        # below) — that pattern means the run was blocked,
                        # not that graduate hiring in the UK is at zero.
                        combos_blocked += 1
                        continue

                    for card_html in session.query_all_html(CARD_SELECTOR):
                        posting = parse_article(card_html)
                        if posting is None or posting.url in seen:
                            continue
                        seen.add(posting.url)
                        postings.append(posting)

                    if len(postings) >= query.limit:
                        break
                if len(postings) >= query.limit:
                    break

        source_errors: list[str] = []
        if combos_tried > 0 and combos_blocked == combos_tried:
            source_errors.append(
                f"gradcracker: all {combos_tried} search(es) blocked — "
                "the challenge likely wasn't passed"
            )

        return JobSearchResult(postings=postings[: query.limit], source_errors=source_errors)

    def health_check(self) -> ProviderHealth:
        # Optimistic, matching NaukriProvider and GreenhouseProvider: a real
        # health probe would mean launching a browser on every registry
        # check, doubling the cost of every search. search() itself reports
        # a fully-blocked run through source_errors.
        return ProviderHealth(status=HealthStatus.HEALTHY)
