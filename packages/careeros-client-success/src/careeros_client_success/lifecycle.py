"""Client lifecycle classification: One Client -> Repeat Client ->
Long-term Client -> Referral. Computed directly from real completed
contract counts and referral records — never a manually-assigned label,
so it can't drift from what actually happened.
"""

from __future__ import annotations

from enum import StrEnum

from careeros_client_success.contract import Contract, ContractStatus

_REPEAT_THRESHOLD = 2
_LONG_TERM_THRESHOLD = 4


class ClientLifecycleStage(StrEnum):
    ONE_TIME = "one_time"
    REPEAT = "repeat"
    LONG_TERM = "long_term"
    REFERRAL_SOURCE = "referral_source"


def classify_client_lifecycle_stage(
    contracts: list[Contract], *, referral_count: int = 0
) -> ClientLifecycleStage | None:
    if referral_count > 0:
        return ClientLifecycleStage.REFERRAL_SOURCE

    completed = [c for c in contracts if c.status == ContractStatus.COMPLETED]
    if not completed:
        return None
    if len(completed) >= _LONG_TERM_THRESHOLD:
        return ClientLifecycleStage.LONG_TERM
    if len(completed) >= _REPEAT_THRESHOLD:
        return ClientLifecycleStage.REPEAT
    return ClientLifecycleStage.ONE_TIME
