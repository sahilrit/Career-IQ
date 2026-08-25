"""careeros_seek_provider: FIND_JOBS over Seek, Australia/NZ's largest board.

Seek's search-results page (``/jobs``) itself is behind bot detection, but
its own frontend calls a plain, unauthenticated JSON API
(``/api/jobsearch/v5/search``) to render it — verified live (2026-08-26):
a bare GET with a normal User-Agent returns real paginated job data, no
key, no browser, no challenge. This provider reads that response directly.
"""

from careeros_seek_provider.parser import (
    API_URL,
    BASE_URL,
    PROVIDER_ID,
    is_job_entry,
    make_job_url,
    parse_job_entry,
    parse_search_response,
)
from careeros_seek_provider.provider import SeekProvider

__all__ = [
    "API_URL",
    "BASE_URL",
    "PROVIDER_ID",
    "SeekProvider",
    "is_job_entry",
    "make_job_url",
    "parse_job_entry",
    "parse_search_response",
]
