"""Registry of freelance providers implementing the FIND_GIGS capability.

Mirrors careeros_job_providers.JobProviderRegistry (Phase 6): the rest of
CareerOS asks for "every healthy FIND_GIGS provider" and aggregates
results, never importing a specific marketplace directly.
"""

from __future__ import annotations

from careeros_common import get_logger
from careeros_freelance_providers.dedupe import deduplicate
from careeros_freelance_providers.filtering import filter_postings
from careeros_freelance_providers.models import GigSearchQuery
from careeros_freelance_providers.provider import (
    FreelanceProvider,
    GigSearchResult,
    HealthStatus,
)

logger = get_logger(__name__)


class FreelanceProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, FreelanceProvider] = {}

    def register(self, provider: FreelanceProvider) -> None:
        self._providers[provider.provider_id] = provider

    def unregister(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)

    def get(self, provider_id: str) -> FreelanceProvider | None:
        return self._providers.get(provider_id)

    def list_all(self) -> list[FreelanceProvider]:
        return list(self._providers.values())

    def healthy_providers(self) -> list[FreelanceProvider]:
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

    def search_all(self, query: GigSearchQuery) -> GigSearchResult:
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
        return GigSearchResult(postings=deduped)
