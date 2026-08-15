"""Registry of job providers implementing the FIND_JOBS capability.

The rest of CareerOS asks the registry for "every healthy FIND_JOBS
provider" and aggregates results — it never imports a specific provider
like RemoteOK directly. Phase 24 (Capability Marketplace) generalizes
this pattern to every capability; this is its first working instance.
"""

from __future__ import annotations

from careeros_common import get_logger
from careeros_job_providers.dedupe import deduplicate
from careeros_job_providers.filtering import filter_postings
from careeros_job_providers.models import JobSearchQuery
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

    def healthy_providers(self) -> list[JobProvider]:
        """Every registered provider whose health check doesn't report DOWN."""
        healthy = []
        for provider in self._providers.values():
            try:
                health = provider.health_check()
            except Exception:
                logger.exception("Health check failed for provider %s", provider.provider_id)
                continue
            if health.status != HealthStatus.DOWN:
                healthy.append(provider)
        return healthy

    def search_all(self, query: JobSearchQuery) -> JobSearchResult:
        """Query every healthy provider, then filter, dedupe, and aggregate results.

        A single provider's search failure is logged and skipped rather
        than failing the whole aggregate search.
        """
        all_postings = []
        for provider in self.healthy_providers():
            try:
                result = provider.search(query)
            except Exception:
                logger.exception("Search failed for provider %s", provider.provider_id)
                continue
            all_postings.extend(result.postings)

        filtered = filter_postings(all_postings, query)
        deduped = deduplicate(filtered)
        return JobSearchResult(postings=deduped)
