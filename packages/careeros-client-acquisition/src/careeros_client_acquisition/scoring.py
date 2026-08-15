"""Opportunity scoring for a qualified company prospect: more detected,
real problems means a stronger pitch and a higher score. Deterministic
and explainable, mirroring careeros_opportunity_intelligence's
score_opportunity (Phase 20).
"""

from __future__ import annotations

from careeros_client_acquisition.signals import ProblemSignal

_POINTS_PER_SIGNAL = 20.0
_MAX_SCORE = 100.0


def score_company_opportunity(signals: list[ProblemSignal]) -> float:
    return min(_MAX_SCORE, len(signals) * _POINTS_PER_SIGNAL)
