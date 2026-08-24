"""HiringCafeProvider: FIND_JOBS over Hiring Cafe's rendered search."""

from __future__ import annotations

from typing import Any

from careeros_hiringcafe_provider.client import (
    HiringCafeTransport,
    HttpxHiringCafeTransport,
)
from careeros_hiringcafe_provider.parser import (
    PROVIDER_ID,
    HiringCafeChallengeError,
    is_job_entry,
    parse_job_entry,
    parse_ssr_page,
)
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)

#: Hiring Cafe serves ~40-50 hits per page; this caps a broad search.
_MAX_PAGES = 6
# Hiring Cafe's free-text query is effectively AND across words, so a long
# multi-keyword blob matches almost nothing. We search each keyword separately
# (OR semantics) and merge — capped so a huge keyword list stays reasonable.
_MAX_KEYWORD_SEARCHES = 6

_WORKPLACE_TYPES = {"remote": "Remote", "hybrid": "Hybrid", "onsite": "Onsite"}


def build_search_state(query: JobSearchQuery, *, search_query: str | None = None) -> dict[str, Any]:
    """Hiring Cafe's whole search lives in one JSON query parameter.

    Locations are folded into the free-text query rather than sent as a
    structured filter: the structured form wants a geocoded city object,
    and a plain place name in the query gets us the same narrowing without
    a geocoding round-trip.
    """
    if search_query is None:
        terms = [term.strip() for term in [*query.keywords, *query.locations] if term.strip()]
        search_query = " ".join(terms)
    state: dict[str, Any] = {"searchQuery": search_query}
    if query.remote_only:
        state["workplaceTypes"] = [_WORKPLACE_TYPES["remote"]]
    return state


class HiringCafeProvider(JobProvider):
    def __init__(
        self,
        transport: HiringCafeTransport | None = None,
        *,
        max_pages: int = _MAX_PAGES,
    ) -> None:
        self._transport = transport or HttpxHiringCafeTransport()
        self._max_pages = max_pages

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        postings: list[JobPosting] = []
        seen: set[str] = set()

        locations = [loc.strip() for loc in query.locations if loc.strip()]
        keywords = [kw.strip() for kw in query.keywords if kw.strip()]
        # One free-text search per keyword (OR semantics), each narrowed by the
        # locations; an empty keyword list falls back to a single broad search.
        search_queries = [
            " ".join([keyword, *locations]).strip()
            for keyword in (keywords[:_MAX_KEYWORD_SEARCHES] or [""])
        ]

        for search_query in search_queries:
            state = build_search_state(query, search_query=search_query)
            for page in range(self._max_pages):
                html = self._transport.fetch_search_page(search_state=state, page=page)
                ssr_page = parse_ssr_page(html)

                for hit in ssr_page.hits:
                    if not is_job_entry(hit):
                        continue
                    posting = parse_job_entry(hit)
                    if posting.external_id in seen:
                        continue
                    seen.add(posting.external_id)
                    postings.append(posting)

                if ssr_page.is_last_page or not ssr_page.hits or len(postings) >= query.limit:
                    break
            if len(postings) >= query.limit:
                break

        # Hiring Cafe matched the keywords against the full posting; we only
        # hold its structured summary, so re-checking would drop real matches.
        filtered = filter_postings(postings, query, applied_server_side={"keywords", "locations"})
        return JobSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            parse_ssr_page(
                self._transport.fetch_search_page(search_state={"searchQuery": ""}, page=0)
            )
        except HiringCafeChallengeError as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
