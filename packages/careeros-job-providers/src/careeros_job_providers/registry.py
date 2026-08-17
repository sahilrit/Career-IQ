"""Registry of job providers implementing the FIND_JOBS capability.

The rest of CareerOS asks the registry for "every healthy FIND_JOBS
provider" and aggregates results — it never imports a specific provider
like RemoteOK directly. Phase 24 (Capability Marketplace) generalizes
this pattern to every capability; this is its first working instance.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from careeros_common import get_logger
from careeros_job_providers.dedupe import deduplicate
from careeros_job_providers.filtering import filter_postings
from careeros_job_providers.models import JobPosting, JobSearchQuery
from careeros_job_providers.provider import HealthStatus, JobProvider, JobSearchResult

logger = get_logger(__name__)


class JobProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, JobProvider] = {}

    def register(self, provider: JobProvider) -> None:
        self._providers[provider.provider_id] = provider

    def unregister(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)

    def get(self, provider_id: str) -> JobProvider | None:
        return self._providers.get(provider_id)

    def list_all(self) -> list[JobProvider]:
        return list(self._providers.values())

    def _is_live(self, provider: JobProvider) -> bool:
        try:
            return provider.health_check().status != HealthStatus.DOWN
        except Exception:
            logger.exception("Health check failed for provider %s", provider.provider_id)
            return False

    def healthy_providers(self) -> list[JobProvider]:
        """Every registered provider whose health check doesn't report DOWN.

        Providers are health-checked concurrently — several of them crawl
        many company boards, so serial checks would dominate wall-clock.
        """
        providers = list(self._providers.values())
        if not providers:
            return []
        with ThreadPoolExecutor(max_workers=len(providers)) as pool:
            live = pool.map(self._is_live, providers)
        return [provider for provider, ok in zip(providers, live, strict=True) if ok]

    def _search_one(self, provider: JobProvider, query: JobSearchQuery) -> list[JobPosting]:
        try:
            return provider.search(query).postings
        except Exception:
            logger.exception("Search failed for provider %s", provider.provider_id)
            return []

    def search_all(self, query: JobSearchQuery) -> JobSearchResult:
        """Query every healthy provider concurrently, then filter, dedupe,
        and aggregate. A single provider's failure is logged and skipped
        rather than failing the whole aggregate search.
        """
        providers = self.healthy_providers()
        all_postings: list[JobPosting] = []
        if providers:
            with ThreadPoolExecutor(max_workers=len(providers)) as pool:
                for postings in pool.map(lambda p: self._search_one(p, query), providers):
                    all_postings.extend(postings)

        filtered = filter_postings(all_postings, query)
        deduped = deduplicate(filtered)
        return JobSearchResult(postings=deduped)
