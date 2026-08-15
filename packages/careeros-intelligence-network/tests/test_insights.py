"""Tests for cross-contribution signal aggregation."""

from __future__ import annotations

from careeros_intelligence_network import SignalCategory, SignalContribution, aggregate_signals


def test_aggregates_only_the_requested_category():
    contributions = [
        SignalContribution(category=SignalCategory.SKILL_DEMAND, label="python", weight=1.0),
        SignalContribution(
            category=SignalCategory.OUTREACH_PATTERN, label="cold_email", weight=1.0
        ),
    ]
    insight = aggregate_signals(contributions, category=SignalCategory.SKILL_DEMAND)
    assert insight.total_contributions == 1
    assert [r.label for r in insight.rankings] == ["python"]


def test_ranks_labels_by_total_weight_descending():
    contributions = [
        SignalContribution(category=SignalCategory.SKILL_DEMAND, label="python", weight=1.0),
        SignalContribution(category=SignalCategory.SKILL_DEMAND, label="rust", weight=5.0),
        SignalContribution(category=SignalCategory.SKILL_DEMAND, label="python", weight=1.0),
    ]
    insight = aggregate_signals(contributions, category=SignalCategory.SKILL_DEMAND)
    assert [r.label for r in insight.rankings] == ["rust", "python"]
    assert insight.rankings[1].total_weight == 2.0
    assert insight.rankings[1].contribution_count == 2


def test_empty_contributions_yields_an_empty_insight():
    insight = aggregate_signals([], category=SignalCategory.SKILL_DEMAND)
    assert insight.rankings == []
    assert insight.total_contributions == 0
