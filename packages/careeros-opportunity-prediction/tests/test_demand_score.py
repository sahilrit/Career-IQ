"""Tests for calculate_predicted_demand."""

from __future__ import annotations

from careeros_opportunity_prediction import DISCLAIMER, PredictionSignal, SignalType
from careeros_opportunity_prediction.demand_score import calculate_predicted_demand


def _signal() -> PredictionSignal:
    return PredictionSignal(company_id="company-1", signal_type=SignalType.FUNDING, detail="d")


def test_no_signals_means_zero_score():
    score = calculate_predicted_demand("company-1", [])
    assert score.score == 0.0
    assert score.signal_count == 0


def test_score_scales_with_signal_count():
    score = calculate_predicted_demand("company-1", [_signal(), _signal()])
    assert score.score == 25.0


def test_score_caps_at_100():
    score = calculate_predicted_demand("company-1", [_signal() for _ in range(10)])
    assert score.score == 100.0


def test_disclaimer_is_present():
    score = calculate_predicted_demand("company-1", [_signal()])
    assert score.disclaimer == DISCLAIMER
