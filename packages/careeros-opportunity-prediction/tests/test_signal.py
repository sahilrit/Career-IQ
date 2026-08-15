"""Tests for PredictionSignal / PredictionSignalRepository."""

from __future__ import annotations

from careeros_opportunity_prediction import PredictionSignal, SignalType


def test_list_for_company_filters(signal_repository):
    matching = PredictionSignal(
        company_id="company-1", signal_type=SignalType.FUNDING, detail="Raised Series B"
    )
    other = PredictionSignal(
        company_id="company-2", signal_type=SignalType.FUNDING, detail="Unrelated"
    )
    signal_repository.save(matching)
    signal_repository.save(other)
    assert signal_repository.list_for_company("company-1") == [matching]
