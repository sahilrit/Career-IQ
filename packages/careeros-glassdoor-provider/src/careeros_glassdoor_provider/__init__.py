"""careeros_glassdoor_provider: FIND_JOBS over Glassdoor.

Glassdoor's search-results page is behind its own bot wall — a plain
request returns a "Security | Glassdoor" block page — but a real
anti-detect (Camoufox) browser session gets through cleanly, confirmed
live (2026-08-26): real listings render, no login wall, no captcha.

Each result renders as a self-contained ``[data-test="job-card-wrapper"]``
card with every field (title, company, location, salary estimate,
description) anchored by a stable ``data-test``/``id`` attribute, even
though the surrounding CSS class names are build-hashed and change on
every deploy — this reads those anchors directly rather than the JSON-LD
``ItemList`` the page also ships, which has only title+url per entry.

Deliberately **not** part of the hosted API's default provider registry
(see docs/plans/browser-gated-sources.md): it needs a real browser and a
real IP, which is what the local autopilot daemon has and the hosted API
does not.
"""

from careeros_glassdoor_provider.parser import BASE_URL, PROVIDER_ID, is_job_entry, parse_card
from careeros_glassdoor_provider.provider import GlassdoorProvider

__all__ = [
    "BASE_URL",
    "PROVIDER_ID",
    "GlassdoorProvider",
    "is_job_entry",
    "parse_card",
]
