"""careeros_ziprecruiter_provider: FIND_JOBS over ZipRecruiter.

ZipRecruiter's search-results page is behind a real Cloudflare challenge —
confirmed passable with a real anti-detect (Camoufox) session (verified
live 2026-08-26). Rather than scraping the rendered DOM's job cards (which
duplicate across a list view and a selected-job detail pane), this reads
the page's own embedded JSON-LD ``ItemList`` structured data, which every
result page ships regardless of layout — one entry per posting, with a
reliable job id, title, and URL to derive company/location from.

Deliberately **not** part of the hosted API's default provider registry
(see docs/plans/browser-gated-sources.md): it needs a real browser and a
real IP, which is what the local autopilot daemon has and the hosted API
does not.
"""

from careeros_ziprecruiter_provider.parser import (
    BASE_URL,
    PROVIDER_ID,
    extract_ld_json_items,
    is_job_entry,
    make_search_url,
    parse_job_entry,
)
from careeros_ziprecruiter_provider.provider import ZipRecruiterProvider

__all__ = [
    "BASE_URL",
    "PROVIDER_ID",
    "ZipRecruiterProvider",
    "extract_ld_json_items",
    "is_job_entry",
    "make_search_url",
    "parse_job_entry",
]
