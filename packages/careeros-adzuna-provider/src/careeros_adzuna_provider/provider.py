"""AdzunaProvider: FIND_JOBS over Adzuna's official multi-country API."""

from __future__ import annotations

from careeros_adzuna_provider.client import (
    ADZUNA_APP_ID_ENV_VAR,
    ADZUNA_APP_KEY_ENV_VAR,
    AdzunaTransport,
    HttpxAdzunaTransport,
    credentials,
)
from careeros_adzuna_provider.countries import country_for_locations
from careeros_adzuna_provider.parser import PROVIDER_ID, is_job_entry, parse_job_entry
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

logger = get_logger(__name__)

_MAX_PAGES = 5
_MISSING_CREDENTIALS = (
    f"{ADZUNA_APP_ID_ENV_VAR} and {ADZUNA_APP_KEY_ENV_VAR} are not set — "
    "register a free key at https://developer.adzuna.com"
)


class AdzunaProvider(JobProvider):
    def __init__(
        self,
        transport: AdzunaTransport | None = None,
        *,
        max_pages: int = _MAX_PAGES,
    ) -> None:
        self._transport = transport or HttpxAdzunaTransport()
        self._max_pages = max_pages

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        if credentials() is None:
            # health_check already reports this; returning empty keeps a
            # credential-less install from failing every search it runs.
            logger.info("Adzuna skipped: %s", _MISSING_CREDENTIALS)
            return JobSearchResult()

        country = country_for_locations(list(query.locations))
        what = " ".join(term.strip() for term in query.keywords if term.strip())
        where = query.locations[0] if query.locations else None

        postings: list[JobPosting] = []
        seen: set[str] = set()

        for page in range(1, self._max_pages + 1):
            results = self._transport.search(
                country=country,
                page=page,
                what=what,
                where=where,
                results_per_page=min(query.limit, 50),
            )
            for result in results:
                if not is_job_entry(result):
                    continue
                posting = parse_job_entry(result)
                if posting.external_id in seen:
                    continue
                seen.add(posting.external_id)
                postings.append(posting)

            if not results or len(postings) >= query.limit:
                break

        # Adzuna matched `what` against the full advert and `where` against its
        # own geocoding; our copy is a snippet, so re-checking would drop hits.
        filtered = filter_postings(postings, query, applied_server_side={"keywords", "locations"})
        return JobSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        if credentials() is None:
            return ProviderHealth(status=HealthStatus.DOWN, detail=_MISSING_CREDENTIALS)
        try:
            self._transport.search(country="gb", page=1, what="", where=None, results_per_page=1)
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
