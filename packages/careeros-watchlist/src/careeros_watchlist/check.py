"""The watchlist check: diff each watched board against what we saw last time.

Run on a schedule, this is what turns "I applied and waited" into "a new
role opened at a company I care about". The design guards two failure
modes that would make it untrustworthy:

* The first check of a board is a silent baseline. Adding a company must
  not alert on its entire existing board.
* An empty or failed fetch is treated as an error, never as "the board was
  wiped" — otherwise a transient blip discards the baseline and the next
  real posting looks new all over again.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from careeros_common import DocumentStore, get_logger
from careeros_event_bus import Event, EventBus
from careeros_job_providers import JobPosting
from careeros_watchlist import boards
from careeros_watchlist.models import ATS, WatchedCompany
from careeros_watchlist.repository import WatchlistRepository

logger = get_logger(__name__)

BoardFetcher = Callable[[WatchedCompany], list[JobPosting]]


class WatchlistCheckResult(BaseModel):
    checked: int = 0
    errored: int = 0
    baselined: int = 0
    new_postings: list[JobPosting] = Field(default_factory=list)


def _check_one(
    company: WatchedCompany,
    *,
    repo: WatchlistRepository,
    fetch: BoardFetcher,
    event_bus: EventBus,
    result: WatchlistCheckResult,
) -> None:
    result.checked += 1
    try:
        postings = fetch(company)
    except Exception as exc:
        result.errored += 1
        logger.warning("Watchlist fetch failed for %s: %s", company.key, exc)
        return

    if not postings:
        # Almost always a transient failure, not an emptied board. Leave the
        # baseline intact so a real posting later still reads as new.
        result.errored += 1
        logger.info("Watchlist board %s returned no postings; leaving baseline", company.key)
        return

    current_ids = {p.external_id for p in postings}

    if not repo.has_baseline(company):
        repo.record_seen(company, current_ids)
        result.baselined += 1
        return

    seen = repo.seen_ids(company)
    new = [p for p in postings if p.external_id not in seen]

    for posting in new:
        result.new_postings.append(posting)
        event_bus.publish(
            Event(
                event_type="watchlist.job_found",
                source="watchlist",
                payload={
                    "ats": company.ats.value,
                    "board_token": company.board_token,
                    "external_id": posting.external_id,
                    "title": posting.title,
                    "url": posting.url,
                },
            )
        )

    # Remember the union: a posting taken down and re-listed should not alert
    # a second time.
    repo.record_seen(company, seen | current_ids)


def check_watchlist(
    store: DocumentStore,
    *,
    event_bus: EventBus,
    fetch: BoardFetcher | None = None,
    only: tuple[ATS, str] | None = None,
) -> WatchlistCheckResult:
    """Check every watched board (or just ``only``) and return what's new.

    ``fetch`` defaults to the real ATS-backed board fetch, resolved at call
    time so a test (or a caller) can substitute its own.
    """
    resolved_fetch = fetch if fetch is not None else boards.fetch_board
    repo = WatchlistRepository(store)
    result = WatchlistCheckResult()

    if only is not None:
        company = repo.get(*only)
        companies = [company] if company is not None else []
    else:
        companies = repo.list_watched()

    for company in companies:
        _check_one(company, repo=repo, fetch=resolved_fetch, event_bus=event_bus, result=result)

    return result
