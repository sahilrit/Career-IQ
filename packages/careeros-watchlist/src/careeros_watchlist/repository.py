"""Persistence for the watchlist: which companies are watched, and which
postings on each board have already been reported."""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_watchlist.models import ATS, WatchedCompany, _SeenBoard

_WATCHED_ENTITY = "watchlist_company"
_SEEN_ENTITY = "watchlist_seen"


class WatchlistRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    # -- watched companies --------------------------------------------------

    def watch(self, ats: ATS, board_token: str, *, display_name: str = "") -> WatchedCompany:
        company = WatchedCompany(ats=ats, board_token=board_token, display_name=display_name)
        # Keyed by ats:token, so re-watching updates rather than duplicates.
        self._store.put(_WATCHED_ENTITY, company.key, company.model_dump(mode="json"))
        return company

    def unwatch(self, ats: ATS, board_token: str) -> None:
        key = WatchedCompany(ats=ats, board_token=board_token).key
        self._store.delete(_WATCHED_ENTITY, key)
        self._store.delete(_SEEN_ENTITY, key)

    def list_watched(self) -> list[WatchedCompany]:
        return [WatchedCompany.model_validate(raw) for raw in self._store.list(_WATCHED_ENTITY)]

    def get(self, ats: ATS, board_token: str) -> WatchedCompany | None:
        key = WatchedCompany(ats=ats, board_token=board_token).key
        raw = self._store.get_or_none(_WATCHED_ENTITY, key)
        return WatchedCompany.model_validate(raw) if raw else None

    # -- seen postings ------------------------------------------------------

    def seen_ids(self, company: WatchedCompany) -> set[str]:
        raw = self._store.get_or_none(_SEEN_ENTITY, company.key)
        return set(_SeenBoard.model_validate(raw).posting_ids) if raw else set()

    def has_baseline(self, company: WatchedCompany) -> bool:
        """Whether this board has ever been checked.

        The first check records a baseline and reports nothing; distinguishing
        "never seen" from "seen, and empty" is what stops the initial add from
        alerting on the whole board.
        """
        return self._store.get_or_none(_SEEN_ENTITY, company.key) is not None

    def record_seen(self, company: WatchedCompany, posting_ids: set[str]) -> None:
        self._store.put(
            _SEEN_ENTITY,
            company.key,
            _SeenBoard(posting_ids=sorted(posting_ids)).model_dump(),
        )
