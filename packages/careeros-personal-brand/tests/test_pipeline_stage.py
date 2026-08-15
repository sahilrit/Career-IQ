"""Tests for ContentProgress / ContentProgressRepository."""

from __future__ import annotations

from careeros_personal_brand import ContentStage


def test_fresh_progress_has_no_current_stage(progress_repository):
    progress = progress_repository.load("project-1")
    assert progress.current_stage is None
    assert progress.next_stage == ContentStage.CASE_STUDY


def test_marking_a_stage_complete_updates_current_and_next(progress_repository):
    progress_repository.mark_complete("project-1", ContentStage.CASE_STUDY)
    progress = progress_repository.load("project-1")
    assert progress.current_stage == ContentStage.CASE_STUDY
    assert progress.next_stage == ContentStage.PORTFOLIO


def test_final_stage_has_no_next_stage(progress_repository):
    progress_repository.mark_complete("project-1", ContentStage.RESUME_ACHIEVEMENT)
    progress = progress_repository.load("project-1")
    assert progress.next_stage is None


def test_progress_is_isolated_per_project(progress_repository):
    progress_repository.mark_complete("project-1", ContentStage.CASE_STUDY)
    other = progress_repository.load("project-2")
    assert other.current_stage is None
