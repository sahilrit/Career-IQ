"""careeros_hiringcafe_provider: FIND_JOBS backed by Hiring Cafe.

Hiring Cafe aggregates postings from thousands of company ATS boards and
publishes its own structured extraction of each one — requirements,
seniority, tools, compensation. There is no public API; the results are
server-rendered into the page, which is what this provider reads.
"""

from careeros_hiringcafe_provider.client import (
    HIRINGCAFE_BASE_URL,
    HiringCafeTransport,
    HttpxHiringCafeTransport,
)
from careeros_hiringcafe_provider.parser import (
    JOB_PAGE_TEMPLATE,
    PROVIDER_ID,
    HiringCafeChallengeError,
    HiringCafeSsrPage,
    is_job_entry,
    parse_job_entry,
    parse_ssr_page,
)
from careeros_hiringcafe_provider.provider import HiringCafeProvider, build_search_state

__all__ = [
    "HIRINGCAFE_BASE_URL",
    "JOB_PAGE_TEMPLATE",
    "PROVIDER_ID",
    "HiringCafeChallengeError",
    "HiringCafeProvider",
    "HiringCafeSsrPage",
    "HiringCafeTransport",
    "HttpxHiringCafeTransport",
    "build_search_state",
    "is_job_entry",
    "parse_job_entry",
    "parse_ssr_page",
]
