"""Fetch one company's live board through the matching ATS adapter.

The adapters already know how to read a single company board — the same code
the aggregate search uses — so the watchlist reuses them scoped to one board
rather than re-implementing per-ATS API clients. Adding an ATS to the watchlist
is now an entry in ``_ADAPTERS``, not a new transport.
"""

from __future__ import annotations

from careeros_ats_providers import ADAPTER_CLASSES, AtsBoardProvider, BoardEntry
from careeros_job_providers import JobPosting, JobSearchQuery
from careeros_watchlist.models import ATS, WatchedCompany

# A board can be large; this is comfortably above any single company's count.
_BOARD_LIMIT = 1000

_ADAPTERS = {
    ATS.GREENHOUSE: "greenhouse",
    ATS.LEVER: "lever",
    ATS.ASHBY: "ashby",
}


def fetch_board(company: WatchedCompany) -> list[JobPosting]:
    """Every current posting on one company's board, via its ATS adapter."""
    ats_id = _ADAPTERS.get(company.ats)
    if ats_id is None:  # pragma: no cover - exhaustive over the enum
        raise ValueError(f"unsupported ATS: {company.ats}")

    entry = BoardEntry(company.board_token, company.name)
    provider = AtsBoardProvider(ADAPTER_CLASSES[ats_id](), [entry])
    # An empty query returns the whole board; the watchlist wants everything,
    # then diffs locally.
    return provider.search(JobSearchQuery(limit=_BOARD_LIMIT)).postings
