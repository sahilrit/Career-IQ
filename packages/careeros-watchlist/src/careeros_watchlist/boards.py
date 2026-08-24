"""Fetch one company's live board through the matching ATS provider.

Each ATS provider already knows how to read a single company board — the
same code the aggregate search uses — so the watchlist reuses them scoped
to one board rather than re-implementing three API clients.
"""

from __future__ import annotations

from careeros_ashby_provider import AshbyProvider, HttpxAshbyTransport
from careeros_greenhouse_provider import GreenhouseProvider, HttpxGreenhouseTransport
from careeros_job_providers import JobPosting, JobSearchQuery
from careeros_lever_provider import HttpxLeverTransport, LeverProvider
from careeros_watchlist.models import ATS, WatchedCompany

# A board can be large; this is comfortably above any single company's count.
_BOARD_LIMIT = 1000


def fetch_board(company: WatchedCompany) -> list[JobPosting]:
    """Every current posting on one company's board, via its ATS provider."""
    token = company.board_token
    if company.ats is ATS.GREENHOUSE:
        provider = GreenhouseProvider(HttpxGreenhouseTransport(companies=(token,)))
    elif company.ats is ATS.LEVER:
        provider = LeverProvider(HttpxLeverTransport(companies=(token,)))
    elif company.ats is ATS.ASHBY:
        provider = AshbyProvider(HttpxAshbyTransport(companies=(token,)))
    else:  # pragma: no cover - exhaustive over the enum
        raise ValueError(f"unsupported ATS: {company.ats}")

    # An empty query returns the whole board; the watchlist wants everything,
    # then diffs locally.
    return provider.search(JobSearchQuery(limit=_BOARD_LIMIT)).postings
