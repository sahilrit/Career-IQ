"""LinkedInProvider: the FIND_JOBS provider for LinkedIn.

Unlike our API-backed providers, LinkedIn has no feed to page through —
one request per keyword per page of 25, stopping as soon as a page comes
back empty. Descriptions cost one extra request each, so they are capped:
the scorer needs description text to be useful, but not for every result.
"""

from __future__ import annotations

import os

from careeros_common import get_logger
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)
from careeros_linkedin_provider.client import (
    PAGE_SIZE,
    HttpxLinkedInTransport,
    LinkedInTransport,
)
from careeros_linkedin_provider.parser import (
    SOURCE_PROVIDER,
    extract_job_cards,
    is_job_entry,
    parse_description_html,
    parse_job_entry,
)

logger = get_logger(__name__)

#: Hard ceiling on requests per keyword, so a broad search can't run away.
_MAX_PAGES_PER_KEYWORD = 8
_DEFAULT_MAX_DESCRIPTIONS = 40
_DESCRIPTIONS_ENV_VAR = "CAREEROS_LINKEDIN_FETCH_DESCRIPTIONS"
_FALSEY = {"0", "false", "no", "off", ""}


def _descriptions_enabled_by_default() -> bool:
    raw = os.environ.get(_DESCRIPTIONS_ENV_VAR)
    if raw is None:
        return True
    return raw.strip().lower() not in _FALSEY


class LinkedInProvider(JobProvider):
    def __init__(
        self,
        transport: LinkedInTransport | None = None,
        *,
        fetch_descriptions: bool | None = None,
        max_descriptions: int = _DEFAULT_MAX_DESCRIPTIONS,
        max_pages_per_keyword: int = _MAX_PAGES_PER_KEYWORD,
    ) -> None:
        self._transport = transport or HttpxLinkedInTransport()
        self._fetch_descriptions = (
            _descriptions_enabled_by_default() if fetch_descriptions is None else fetch_descriptions
        )
        self._max_descriptions = max_descriptions
        self._max_pages_per_keyword = max_pages_per_keyword

    @property
    def provider_id(self) -> str:
        return SOURCE_PROVIDER

    def _search_terms(self, query: JobSearchQuery) -> list[str]:
        """One search per keyword. An empty keyword list still searches once —
        LinkedIn treats a blank query as "everything", which with a location
        filter is a reasonable broad sweep."""
        return [term for term in query.keywords if term.strip()] or [""]

    def _cards_for_term(self, term: str, location: str | None, wanted: int) -> list[dict]:
        cards: list[dict] = []
        for page in range(self._max_pages_per_keyword):
            html = self._transport.fetch_search_page(
                keywords=term, location=location, start=page * PAGE_SIZE
            )
            page_cards = [card for card in extract_job_cards(html) if is_job_entry(card)]
            cards.extend(page_cards)
            # An empty page is LinkedIn's end-of-results signal; there is no
            # total count to read.
            if not page_cards or len(cards) >= wanted:
                break
        return cards

    def _describe(self, posting: JobPosting) -> JobPosting:
        try:
            html = self._transport.fetch_job_page(posting.external_id)
        except Exception as exc:
            # A missing description is a quality loss, never a lost posting.
            logger.warning("LinkedIn description fetch failed for %s: %s", posting.external_id, exc)
            return posting
        return posting.model_copy(update={"description": parse_description_html(html)})

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        location = query.locations[0] if query.locations else None
        seen: set[str] = set()
        postings: list[JobPosting] = []

        for term in self._search_terms(query):
            for card in self._cards_for_term(term, location, query.limit):
                job_id = str(card["job_id"])
                if job_id in seen:
                    continue
                seen.add(job_id)
                postings.append(parse_job_entry(card))

        # LinkedIn matched the keywords against full job text and applied the
        # location in its own query. Re-checking either here would drop good
        # results, since descriptions have not been fetched yet at this point.
        filtered = filter_postings(postings, query, applied_server_side={"keywords", "locations"})[
            : query.limit
        ]

        if self._fetch_descriptions:
            filtered = [
                self._describe(posting) if index < self._max_descriptions else posting
                for index, posting in enumerate(filtered)
            ]

        return JobSearchResult(postings=filtered)

    def health_check(self) -> ProviderHealth:
        """One page-one request. Cheap enough to run before every search, and
        the only thing that reliably tells us whether we're being blocked."""
        try:
            self._transport.fetch_search_page(keywords="", location=None, start=0)
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
