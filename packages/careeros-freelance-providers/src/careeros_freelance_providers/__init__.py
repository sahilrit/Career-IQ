"""careeros_freelance_providers: the standardized FIND_GIGS provider SDK.

The rest of CareerOS depends on ``FreelanceProvider``/
``FreelanceProviderRegistry``, never on a specific marketplace like
Fiverr or Upwork directly.
"""

from careeros_freelance_providers.dedupe import deduplicate
from careeros_freelance_providers.exceptions import FreelanceProviderError
from careeros_freelance_providers.filtering import filter_postings, matches_query
from careeros_freelance_providers.models import Budget, GigPosting, GigSearchQuery, ProjectType
from careeros_freelance_providers.provider import (
    CAPABILITY_FIND_GIGS,
    FreelanceProvider,
    GigSearchResult,
    HealthStatus,
    ProviderHealth,
)
from careeros_freelance_providers.registry import FreelanceProviderRegistry

__all__ = [
    "CAPABILITY_FIND_GIGS",
    "Budget",
    "FreelanceProvider",
    "FreelanceProviderError",
    "FreelanceProviderRegistry",
    "GigPosting",
    "GigSearchQuery",
    "GigSearchResult",
    "HealthStatus",
    "ProjectType",
    "ProviderHealth",
    "deduplicate",
    "filter_postings",
    "matches_query",
]
