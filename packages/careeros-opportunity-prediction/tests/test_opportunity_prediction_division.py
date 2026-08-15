"""Tests for the OpportunityPredictionDivision facade."""

from __future__ import annotations

import pytest

from careeros_opportunity_prediction import (
    DecisionMaker,
    OpportunityPredictionDivision,
    PredictionSignal,
    PredictionStage,
    SignalType,
)


@pytest.fixture
def division(signal_repository, decision_maker_repository, progress_repository):
    return OpportunityPredictionDivision(
        signal_repository, decision_maker_repository, progress_repository
    )


def test_record_signal_marks_signal_detected(division):
    division.record_signal(
        PredictionSignal(company_id="company-1", signal_type=SignalType.FUNDING, detail="d")
    )
    assert division.progress_for("company-1").current_stage == PredictionStage.SIGNAL_DETECTED


def test_predict_demand_marks_demand_predicted_when_signals_exist(division):
    division.record_signal(
        PredictionSignal(company_id="company-1", signal_type=SignalType.FUNDING, detail="d")
    )
    score = division.predict_demand("company-1")
    assert score.score > 0
    assert division.progress_for("company-1").current_stage == PredictionStage.DEMAND_PREDICTED


def test_predict_demand_does_not_mark_stage_when_no_signals(division):
    division.predict_demand("company-1")
    assert division.progress_for("company-1").current_stage is None


def test_identify_decision_maker_marks_the_stage(division):
    division.identify_decision_maker(DecisionMaker(company_id="company-1", name="Jane Smith"))
    assert (
        division.progress_for("company-1").current_stage
        == PredictionStage.DECISION_MAKER_IDENTIFIED
    )


def test_full_chain_reaches_positioned(division):
    division.record_signal(
        PredictionSignal(company_id="company-1", signal_type=SignalType.FUNDING, detail="d")
    )
    division.predict_demand("company-1")
    division.mark_researched("company-1")
    division.identify_decision_maker(DecisionMaker(company_id="company-1", name="Jane Smith"))
    division.mark_relationship_started("company-1")
    division.mark_positioned("company-1")
    assert division.progress_for("company-1").current_stage == PredictionStage.POSITIONED
