"""Tests for the company watchlist: watch a board, diff it, surface new jobs.

The board fetch is injected, so the whole diff loop runs against fixtures
with no network. What matters here is the diffing and the bookkeeping —
that a job is reported new exactly once, and that a board going dark is
not read as "every job disappeared".
"""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_job_providers import JobPosting
from careeros_watchlist import (
    ATS,
    WatchedCompany,
    WatchlistRepository,
    check_watchlist,
)


def _posting(external_id: str, title: str = "Growth Lead") -> JobPosting:
    return JobPosting(
        source_provider="greenhouse",
        external_id=external_id,
        title=title,
        company_name="Acme",
        url=f"https://boards.greenhouse.io/acme/jobs/{external_id}",
    )


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def repo(store):
    return WatchlistRepository(store)


def _fetcher(boards: dict[str, list[JobPosting]]):
    """Build a fetch function keyed by (ats, board_token)."""

    def fetch(company: WatchedCompany) -> list[JobPosting]:
        return boards.get(company.board_token, [])

    return fetch


# --- repository --------------------------------------------------------------


def test_watch_and_list_companies(repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    repo.watch(ATS.LEVER, "widgetco", display_name="WidgetCo")
    watched = repo.list_watched()
    assert {c.board_token for c in watched} == {"acme", "widgetco"}


def test_watching_the_same_board_twice_does_not_duplicate(repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme Corp")
    assert len(repo.list_watched()) == 1


def test_the_same_token_on_two_ats_are_distinct(repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    repo.watch(ATS.ASHBY, "acme", display_name="Acme")
    assert len(repo.list_watched()) == 2


def test_unwatch_removes_a_company(repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    repo.unwatch(ATS.GREENHOUSE, "acme")
    assert repo.list_watched() == []


# --- first check -------------------------------------------------------------


def test_the_first_check_reports_nothing_new(store, repo):
    """The first sight of a board is the baseline, not a flood of 'new' jobs.
    Someone who just added a company should not get alerted about its entire
    existing board."""
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    fetch = _fetcher({"acme": [_posting("1"), _posting("2")]})

    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())

    assert result.new_postings == []
    assert result.checked == 1


def test_a_job_appearing_after_the_baseline_is_new(store, repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    boards = {"acme": [_posting("1")]}
    fetch = _fetcher(boards)

    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline
    boards["acme"] = [_posting("1"), _posting("2", title="New Role")]
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())

    assert [p.external_id for p in result.new_postings] == ["2"]


def test_a_job_is_only_reported_new_once(store, repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    boards = {"acme": [_posting("1")]}
    fetch = _fetcher(boards)

    check_watchlist(store, fetch=fetch, event_bus=EventBus())
    boards["acme"] = [_posting("1"), _posting("2")]
    first = check_watchlist(store, fetch=fetch, event_bus=EventBus())
    second = check_watchlist(store, fetch=fetch, event_bus=EventBus())

    assert len(first.new_postings) == 1
    assert second.new_postings == []


def test_a_removed_job_is_not_reported_and_does_not_resurface(store, repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    boards = {"acme": [_posting("1"), _posting("2")]}
    fetch = _fetcher(boards)

    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline {1,2}
    boards["acme"] = [_posting("1")]  # 2 taken down
    check_watchlist(store, fetch=fetch, event_bus=EventBus())
    boards["acme"] = [_posting("1"), _posting("2")]  # 2 reposted
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())

    # 2 was seen before; a re-post is not a new job.
    assert result.new_postings == []


def test_an_empty_board_is_treated_as_an_error_not_a_wipe(store, repo):
    """A board that returns nothing is almost always a transient fetch failure,
    not a company that fired everyone. Never overwrite a good baseline with an
    empty one, or the next real posting looks brand new again."""
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    boards = {"acme": [_posting("1"), _posting("2")]}
    fetch = _fetcher(boards)

    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline {1,2}
    boards["acme"] = []  # board went dark
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())
    assert result.errored == 1

    boards["acme"] = [_posting("1"), _posting("2")]  # back
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())
    assert result.new_postings == []  # baseline was preserved


def test_a_fetch_that_raises_is_isolated(store, repo):
    repo.watch(ATS.GREENHOUSE, "good", display_name="Good")
    repo.watch(ATS.LEVER, "bad", display_name="Bad")

    def fetch(company: WatchedCompany):
        if company.board_token == "bad":
            raise RuntimeError("board 500")
        return [_posting("1")]

    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline for good
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())

    assert result.errored == 1
    assert result.checked == 2


def test_a_new_job_publishes_an_event(store, repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    boards = {"acme": [_posting("1")]}
    fetch = _fetcher(boards)
    bus = EventBus()
    seen: list = []
    bus.subscribe("watchlist.job_found", seen.append)

    check_watchlist(store, fetch=fetch, event_bus=bus)
    boards["acme"] = [_posting("1"), _posting("2")]
    check_watchlist(store, fetch=fetch, event_bus=bus)

    assert len(seen) == 1
    assert seen[0].payload["external_id"] == "2"
    assert seen[0].payload["board_token"] == "acme"


def test_check_only_touches_the_requested_company(store, repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    repo.watch(ATS.LEVER, "widgetco", display_name="WidgetCo")
    calls: list[str] = []

    def fetch(company: WatchedCompany):
        calls.append(company.board_token)
        return [_posting("1")]

    check_watchlist(store, fetch=fetch, event_bus=EventBus(), only=(ATS.LEVER, "widgetco"))

    assert calls == ["widgetco"]


# --- seen-set bounding (regression: unbounded growth) ------------------------


def _seen_size(repo, ats, token) -> int:
    company = repo.get(ats, token)
    return len(repo.seen_ids(company))


def test_seen_set_stays_bounded_as_a_board_churns(store, repo):
    """A long-lived watch on a churning board must not accumulate every id ever
    seen. Current postings are always kept; departed ones are capped."""
    from careeros_watchlist.check import MAX_DEPARTED_RETAINED

    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    board = {"acme": [_posting("0")]}
    fetch = _fetcher(board)
    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline

    # Each cycle fully replaces the board with one fresh posting; the previous
    # one departs. Over many cycles the departed set must stay capped.
    for i in range(1, MAX_DEPARTED_RETAINED + 50):
        board["acme"] = [_posting(str(i))]
        check_watchlist(store, fetch=fetch, event_bus=EventBus())

    seen = _seen_size(repo, ATS.GREENHOUSE, "acme")
    # current (1) + at most the departed cap.
    assert seen <= MAX_DEPARTED_RETAINED + 1


def test_a_recently_departed_posting_does_not_re_alert(store, repo):
    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    board = {"acme": [_posting("1"), _posting("2")]}
    fetch = _fetcher(board)
    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline {1,2}

    board["acme"] = [_posting("1")]  # 2 departs
    check_watchlist(store, fetch=fetch, event_bus=EventBus())
    board["acme"] = [_posting("1"), _posting("2")]  # 2 comes right back
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())

    # 2 was seen recently, so its return is not a new job.
    assert result.new_postings == []


def test_current_postings_are_always_retained(store, repo):
    """However big the board, every currently-listed posting stays in seen, so
    no current posting is ever wrongly re-alerted."""
    from careeros_watchlist.check import MAX_DEPARTED_RETAINED

    repo.watch(ATS.GREENHOUSE, "acme", display_name="Acme")
    big_board = [_posting(str(i)) for i in range(MAX_DEPARTED_RETAINED + 200)]
    fetch = _fetcher({"acme": big_board})
    check_watchlist(store, fetch=fetch, event_bus=EventBus())  # baseline
    result = check_watchlist(store, fetch=fetch, event_bus=EventBus())
    assert result.new_postings == []
