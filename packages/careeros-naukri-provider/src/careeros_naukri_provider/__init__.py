"""careeros_naukri_provider: FIND_JOBS over Naukri, India's largest board.

Naukri's search API requires a real browser session — a plain HTTP
request returns HTTP 406 "recaptcha required" (verified live). This
provider drives an anti-detect Camoufox session to the search page and
reads the JSON response the page's own script fetches, rather than
scraping rendered markup.

Deliberately **not** part of the hosted API's default provider registry
(see docs/plans/browser-gated-sources.md): it needs a real IP and a real
browser, which is what the local autopilot daemon has and the hosted API
does not. Register it explicitly wherever that's true:
``registry.register(NaukriProvider())``.
"""

from careeros_naukri_provider.parser import (
    BASE_URL,
    PROVIDER_ID,
    is_job_entry,
    make_search_url,
    parse_job_entry,
    parse_search_response,
)
from careeros_naukri_provider.provider import NaukriProvider

__all__ = [
    "BASE_URL",
    "PROVIDER_ID",
    "NaukriProvider",
    "is_job_entry",
    "make_search_url",
    "parse_job_entry",
    "parse_search_response",
]
