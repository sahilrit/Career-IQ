"""Tests for ClientAcquisitionProgress / ClientAcquisitionProgressRepository."""

from __future__ import annotations

from careeros_client_acquisition import ClientAcquisitionStage


def test_fresh_progress_has_no_current_stage(progress_repository):
    progress = progress_repository.load("company-1")
    assert progress.current_stage is None
    assert progress.next_stage == ClientAcquisitionStage.DISCOVERY


def test_marking_a_stage_complete_updates_current_and_next(progress_repository):
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.DISCOVERY)
    progress = progress_repository.load("company-1")
    assert progress.current_stage == ClientAcquisitionStage.DISCOVERY
    assert progress.next_stage == ClientAcquisitionStage.QUALIFICATION


def test_current_stage_is_the_furthest_reached_regardless_of_marking_order(progress_repository):
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.AUDIT)
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.DISCOVERY)
    progress = progress_repository.load("company-1")
    assert progress.current_stage == ClientAcquisitionStage.AUDIT


def test_marking_the_same_stage_twice_does_not_duplicate(progress_repository):
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.DISCOVERY)
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.DISCOVERY)
    progress = progress_repository.load("company-1")
    assert progress.completed_stages.count(ClientAcquisitionStage.DISCOVERY) == 1


def test_final_stage_has_no_next_stage(progress_repository):
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.CLIENT)
    progress = progress_repository.load("company-1")
    assert progress.next_stage is None


def test_progress_is_isolated_per_company(progress_repository):
    progress_repository.mark_complete("company-1", ClientAcquisitionStage.DISCOVERY)
    other = progress_repository.load("company-2")
    assert other.current_stage is None
