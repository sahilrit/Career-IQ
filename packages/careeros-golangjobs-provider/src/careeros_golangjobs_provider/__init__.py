"""careeros_golangjobs_provider: FIND_JOBS over golangjobs.tech.

The board is served from a public Supabase PostgREST endpoint with the
site's own anon key — no account, no paid plan. Adds Go-developer roles to
the discovery pool, following the same provider contract as every other
source.
"""

from careeros_golangjobs_provider.client import (
    JOBS_ENDPOINT,
    SUPABASE_URL,
    GolangJobsTransport,
    HttpxGolangJobsTransport,
    anon_key,
)
from careeros_golangjobs_provider.parser import PROVIDER_ID, is_job_entry, parse_job_entry
from careeros_golangjobs_provider.provider import GolangJobsProvider

__all__ = [
    "JOBS_ENDPOINT",
    "PROVIDER_ID",
    "SUPABASE_URL",
    "GolangJobsProvider",
    "GolangJobsTransport",
    "HttpxGolangJobsTransport",
    "anon_key",
    "is_job_entry",
    "parse_job_entry",
]
