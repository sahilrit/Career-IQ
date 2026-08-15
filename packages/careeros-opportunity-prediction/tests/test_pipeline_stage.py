"""Tests for PredictionProgress / PredictionProgressRepository."""

from __future__ import annotations

from careeros_opportunity_prediction import PredictionStage


def test_fresh_progress_has_no_current_stage(progress_repository):
    progress = progress_repository.load("company-1")
    assert progress.current_stage is None
    assert progress.next_stage == PredictionStage.SIGNAL_DETECTED


def test_marking_a_stage_complete_updates_current_and_next(progress_repository):
    progress_repository.mark_complete("company-1", PredictionStage.SIGNAL_DETECTED)
    progress = progress_repository.load("company-1")
    assert progress.current_stage == PredictionStage.SIGNAL_DETECTED
    assert progress.next_stage == PredictionStage.DEMAND_PREDICTED


def test_final_stage_has_no_next_stage(progress_repository):
    progress_repository.mark_complete("company-1", PredictionStage.POSITIONED)
    progress = progress_repository.load("company-1")
    assert progress.next_stage is None


def test_progress_is_isolated_per_company(progress_repository):
    progress_repository.mark_complete("company-1", PredictionStage.SIGNAL_DETECTED)
    other = progress_repository.load("company-2")
    assert other.current_stage is None
