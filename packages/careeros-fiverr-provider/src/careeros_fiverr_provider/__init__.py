"""careeros_fiverr_provider: a second FIND_GIGS provider, browser-driven
since Fiverr has no free public API — proves careeros_freelance_providers'
architecture (Phase 18) generalizes beyond a single marketplace.
"""

from careeros_fiverr_provider.parser import parse_listing
from careeros_fiverr_provider.provider import FiverrProvider
from careeros_fiverr_provider.selectors import FiverrSelectors
from careeros_fiverr_provider.transport import (
    FIVERR_SEARCH_URL,
    BrowserFiverrTransport,
    FiverrTransport,
)

__all__ = [
    "FIVERR_SEARCH_URL",
    "BrowserFiverrTransport",
    "FiverrProvider",
    "FiverrSelectors",
    "FiverrTransport",
    "parse_listing",
]
