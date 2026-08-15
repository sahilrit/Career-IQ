"""Network insights: pure aggregation over already-anonymous
contributions — ranks labels within a category by total weight, the
same combinator philosophy as Phase 40's Career Intelligence, just
across tenants instead of within one.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_intelligence_network.signals import SignalCategory, SignalContribution


class LabelRanking(BaseModel):
    label: str
    total_weight: float
    contribution_count: int


class NetworkInsight(BaseModel):
    category: SignalCategory
    rankings: list[LabelRanking]
    total_contributions: int


def aggregate_signals(
    contributions: list[SignalContribution], *, category: SignalCategory
) -> NetworkInsight:
    relevant = [c for c in contributions if c.category == category]
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for contribution in relevant:
        totals[contribution.label] = totals.get(contribution.label, 0.0) + contribution.weight
        counts[contribution.label] = counts.get(contribution.label, 0) + 1

    rankings = sorted(
        (
            LabelRanking(label=label, total_weight=total, contribution_count=counts[label])
            for label, total in totals.items()
        ),
        key=lambda ranking: ranking.total_weight,
        reverse=True,
    )
    return NetworkInsight(category=category, rankings=rankings, total_contributions=len(relevant))
