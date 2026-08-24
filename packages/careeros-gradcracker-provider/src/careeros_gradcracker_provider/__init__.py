"""careeros_gradcracker_provider: FIND_JOBS over Gradcracker, a UK
graduate-STEM job board.

Gradcracker is Cloudflare-protected — a plain HTTP request returns 403
(verified live). This provider drives an anti-detect Camoufox session to
each role/region search page and parses the rendered job cards.

Deliberately **not** part of the hosted API's default provider registry
(see docs/plans/browser-gated-sources.md): it needs a real IP and a real
browser, which is what the local autopilot daemon has and the hosted API
does not. Register it explicitly wherever that's true:
``registry.register(GradcrackerProvider())``.
"""

from careeros_gradcracker_provider.parser import (
    BASE_URL,
    CARD_SELECTOR,
    PROVIDER_ID,
    is_job_entry,
    make_search_url,
    parse_article,
)
from careeros_gradcracker_provider.provider import (
    DEFAULT_REGIONS,
    DEFAULT_ROLES,
    GradcrackerProvider,
)

__all__ = [
    "BASE_URL",
    "CARD_SELECTOR",
    "DEFAULT_REGIONS",
    "DEFAULT_ROLES",
    "PROVIDER_ID",
    "GradcrackerProvider",
    "is_job_entry",
    "make_search_url",
    "parse_article",
]
