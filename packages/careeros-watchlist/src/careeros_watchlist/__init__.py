"""careeros_watchlist: monitor named companies' hiring boards.

Watch a company and CareerOS checks its ATS board on a schedule, so a new
role at a place you care about reaches you the day it posts — no daily
manual checking. Backed by the Greenhouse, Lever and Ashby providers we
already ship; Lever and Ashby are boards JobOps' watchlist cannot reach.

The check is safe to run repeatedly: the first sight of a board is a
silent baseline, each new posting is reported exactly once, and a board
that fails to load never discards what we already knew.
"""

from careeros_watchlist.boards import fetch_board
from careeros_watchlist.check import (
    MAX_DEPARTED_RETAINED,
    BoardFetcher,
    WatchlistCheckResult,
    check_watchlist,
)
from careeros_watchlist.models import ATS, WatchedCompany
from careeros_watchlist.repository import WatchlistRepository

__all__ = [
    "ATS",
    "MAX_DEPARTED_RETAINED",
    "BoardFetcher",
    "WatchedCompany",
    "WatchlistCheckResult",
    "WatchlistRepository",
    "check_watchlist",
    "fetch_board",
]
