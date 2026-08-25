"""careeros_ukvisajobs_provider: FIND_JOBS over UK Visa Jobs.

UK Visa Jobs requires a credentialed login with the *user's own*
my.ukvisajobs.com email/password — its search API rejects an unauthenticated
request outright. This provider logs in through a real anti-detect browser
session (the login page is a client-rendered SPA behind Cloudflare) to get a
short-lived token and session cookies, then makes plain HTTP calls for the
actual paginated search — no browser needed once authenticated.

Deliberately **not** part of the hosted API's default provider registry
(see docs/plans/browser-gated-sources.md): it needs a real browser for login
and, more importantly, the user's own third-party credentials, which only
the local autopilot daemon (running on the user's own machine) should ever
handle. Register it explicitly wherever that's true.
"""

from careeros_ukvisajobs_provider.parser import (
    API_URL,
    BASE_URL,
    OPEN_JOBS_URL,
    PROVIDER_ID,
    SIGNIN_URL,
    is_job_entry,
    parse_job_entry,
    parse_search_response,
)
from careeros_ukvisajobs_provider.provider import UkVisaJobsProvider

__all__ = [
    "API_URL",
    "BASE_URL",
    "OPEN_JOBS_URL",
    "PROVIDER_ID",
    "SIGNIN_URL",
    "UkVisaJobsProvider",
    "is_job_entry",
    "parse_job_entry",
    "parse_search_response",
]
