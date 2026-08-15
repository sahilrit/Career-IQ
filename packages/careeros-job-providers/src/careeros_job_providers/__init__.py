"""careeros_job_providers: the standardized FIND_JOBS provider SDK.

The rest of CareerOS depends on ``JobProvider``/``JobProviderRegistry``,
never on a specific source like RemoteOK or LinkedIn directly.
"""

from careeros_job_providers.dedupe import deduplicate
from careeros_job_providers.exceptions import JobProviderError
from careeros_job_providers.filtering import filter_postings, matches_query
from careeros_job_providers.models import EmploymentType, JobPosting, JobSearchQuery, Salary
from careeros_job_providers.provider import (
    CAPABILITY_FIND_JOBS,
    HealthStatus,
    JobProvider,
    JobSearchResult,
    ProviderHealth,
)
from careeros_job_providers.registry import JobProviderRegistry

__all__ = [
    "CAPABILITY_FIND_JOBS",
    "EmploymentType",
    "HealthStatus",
    "JobPosting",
    "JobProvider",
    "JobProviderError",
    "JobProviderRegistry",
    "JobSearchQuery",
    "JobSearchResult",
    "ProviderHealth",
    "Salary",
    "deduplicate",
    "filter_postings",
    "matches_query",
]
