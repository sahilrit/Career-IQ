"""careeros_workingnomads_provider: FIND_JOBS backed by Working Nomads.

This reads the search backend that the site's own job search calls, not
the thin ``/api/exposed_jobs/`` feed we used originally. The feed had no
salary, no publish date, and no relevance ranking — it was the whole
catalogue, and we filtered it locally. The search backend takes the query
itself and returns ranked results with salary, tags, publish date and
experience level, which the match scorer can actually use.

Everything is remote by definition here; Working Nomads only lists
remote roles.
"""

from careeros_workingnomads_provider.client import (
    WORKINGNOMADS_SEARCH_URL,
    HttpxWorkingNomadsTransport,
    WorkingNomadsTransport,
    build_search_body,
)
from careeros_workingnomads_provider.parser import (
    PROVIDER_ID,
    is_job_entry,
    parse_job_entry,
)
from careeros_workingnomads_provider.provider import WorkingNomadsProvider

#: Kept for callers that imported the old feed URL by name.
WORKINGNOMADS_API = WORKINGNOMADS_SEARCH_URL

__all__ = [
    "PROVIDER_ID",
    "WORKINGNOMADS_API",
    "WORKINGNOMADS_SEARCH_URL",
    "HttpxWorkingNomadsTransport",
    "WorkingNomadsProvider",
    "WorkingNomadsTransport",
    "build_search_body",
    "is_job_entry",
    "parse_job_entry",
]
