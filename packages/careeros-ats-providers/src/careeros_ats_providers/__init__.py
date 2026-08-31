"""careeros_ats_providers: hosted-ATS job discovery.

One engine, nine adapters. These are the sources whose postings link to open
application forms — no login wall, no captcha — which makes them the only ones
the application engine can realistically fill end to end.
"""

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.adapters import ADAPTER_CLASSES
from careeros_ats_providers.boards import (
    ashby_boards,
    bamboohr_boards,
    greenhouse_boards,
    lever_boards,
    personio_boards,
    recruitee_boards,
    smartrecruiters_boards,
    workable_boards,
    workday_boards,
)
from careeros_ats_providers.http import AtsHttp, BoardFetchError, assert_allowed
from careeros_ats_providers.normalize import (
    annualized_salary,
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)
from careeros_ats_providers.provider import AtsBoardProvider

_BOARD_LOADERS = {
    "greenhouse": greenhouse_boards,
    "lever": lever_boards,
    "ashby": ashby_boards,
    "smartrecruiters": smartrecruiters_boards,
    "workable": workable_boards,
    "recruitee": recruitee_boards,
    "personio": personio_boards,
    "bamboohr": bamboohr_boards,
    "workday": workday_boards,
}


def build_ats_providers(
    *, only: list[str] | None = None, http: AtsHttp | None = None
) -> list[AtsBoardProvider]:
    """One provider per ATS that has at least one configured board.

    An ATS with no boards is skipped rather than registered empty: a provider
    that can never return anything is noise in health output and in the
    per-source error list.
    """
    shared = http or AtsHttp()
    providers: list[AtsBoardProvider] = []
    for ats_id, adapter_class in ADAPTER_CLASSES.items():
        if only is not None and ats_id not in only:
            continue
        boards = _BOARD_LOADERS[ats_id]()
        if not boards:
            continue
        providers.append(AtsBoardProvider(adapter_class(), boards, http=shared))
    return providers


__all__ = [
    "ADAPTER_CLASSES",
    "AtsAdapter",
    "AtsBoardProvider",
    "AtsHttp",
    "BoardEntry",
    "BoardFetchError",
    "annualized_salary",
    "ashby_boards",
    "assert_allowed",
    "bamboohr_boards",
    "build_ats_providers",
    "greenhouse_boards",
    "html_to_text",
    "lever_boards",
    "looks_remote",
    "merge_locations",
    "personio_boards",
    "recruitee_boards",
    "smartrecruiters_boards",
    "to_datetime",
    "workable_boards",
    "workday_boards",
]
