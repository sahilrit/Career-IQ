"""careeros_linkedin_provider: a FIND_JOBS provider backed by LinkedIn's
public logged-out job search endpoint — no account, no API key.

This is the first provider that reads a site rather than an API, so it
carries the extra machinery that implies: an HTML parser, deliberate
request throttling, and a per-search cap on description fetches.
"""

from careeros_linkedin_provider.client import (
    LINKEDIN_JOB_VIEW_URL,
    LINKEDIN_SEARCH_URL,
    PAGE_SIZE,
    HttpxLinkedInTransport,
    LinkedInTransport,
)
from careeros_linkedin_provider.parser import (
    SOURCE_PROVIDER,
    extract_job_cards,
    is_job_entry,
    is_remote_location,
    parse_description_html,
    parse_job_entry,
    parse_salary,
)
from careeros_linkedin_provider.provider import LinkedInProvider

__all__ = [
    "LINKEDIN_JOB_VIEW_URL",
    "LINKEDIN_SEARCH_URL",
    "PAGE_SIZE",
    "SOURCE_PROVIDER",
    "HttpxLinkedInTransport",
    "LinkedInProvider",
    "LinkedInTransport",
    "extract_job_cards",
    "is_job_entry",
    "is_remote_location",
    "parse_description_html",
    "parse_job_entry",
    "parse_salary",
]
