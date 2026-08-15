"""Tests for compute_variant_metrics / VariantMetrics."""

from __future__ import annotations

from careeros_learning_lab import OutcomeEvent, OutcomeType, compute_variant_metrics


def _events(*outcome_types: OutcomeType, revenue: float = 0.0) -> list[OutcomeEvent]:
    events = [OutcomeEvent(variant_id="variant-1", outcome_type=t) for t in outcome_types]
    if revenue:
        events.append(
            OutcomeEvent(variant_id="variant-1", outcome_type=OutcomeType.REVENUE, value=revenue)
        )
    return events


def test_counts_each_outcome_type():
    events = _events(
        OutcomeType.SENT,
        OutcomeType.SENT,
        OutcomeType.RESPONSE,
        OutcomeType.INTERVIEW,
        OutcomeType.OFFER,
        OutcomeType.CLIENT_CONVERSION,
    )
    metrics = compute_variant_metrics("variant-1", events)
    assert metrics.sent_count == 2
    assert metrics.response_count == 1
    assert metrics.interview_count == 1
    assert metrics.offer_count == 1
    assert metrics.client_conversion_count == 1


def test_rates_are_none_when_nothing_was_sent():
    metrics = compute_variant_metrics("variant-1", [])
    assert metrics.response_rate is None
    assert metrics.interview_rate is None


def test_rates_divide_by_sent_count():
    events = _events(OutcomeType.SENT, OutcomeType.SENT, OutcomeType.SENT, OutcomeType.RESPONSE)
    metrics = compute_variant_metrics("variant-1", events)
    assert metrics.response_rate == 1 / 3


def test_total_revenue_sums_revenue_events():
    events = _events(OutcomeType.SENT, revenue=500.0)
    metrics = compute_variant_metrics("variant-1", events)
    assert metrics.total_revenue == 500.0


def test_score_for_maps_outcome_type_to_the_right_field():
    events = _events(OutcomeType.SENT, OutcomeType.SENT, OutcomeType.RESPONSE, revenue=100.0)
    metrics = compute_variant_metrics("variant-1", events)
    assert metrics.score_for(OutcomeType.SENT) == 2.0
    assert metrics.score_for(OutcomeType.RESPONSE) == metrics.response_rate
    assert metrics.score_for(OutcomeType.REVENUE) == 100.0
