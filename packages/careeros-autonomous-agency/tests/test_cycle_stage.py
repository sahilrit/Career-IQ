"""Tests for AgencyCycleProgress / AgencyCycleProgressRepository."""

from __future__ import annotations

import pytest

from careeros_autonomous_agency import (
    AgencyCycleProgressRepository,
    AgencyStage,
    CycleNotCompleteError,
)


def test_new_subject_has_no_current_stage_and_starts_at_employment(store):
    repository = AgencyCycleProgressRepository(store)
    progress = repository.load("subject-1")
    assert progress.current_stage is None
    assert progress.next_stage == AgencyStage.EMPLOYMENT
    assert progress.is_cycle_complete is False


def test_mark_complete_advances_current_and_next_stage(store):
    repository = AgencyCycleProgressRepository(store)
    progress = repository.mark_complete("subject-1", AgencyStage.EMPLOYMENT)
    assert progress.current_stage == AgencyStage.EMPLOYMENT
    assert progress.next_stage == AgencyStage.FREELANCE


def test_current_stage_is_the_furthest_reached_regardless_of_order(store):
    repository = AgencyCycleProgressRepository(store)
    repository.mark_complete("subject-1", AgencyStage.CAREER_INTELLIGENCE)
    repository.mark_complete("subject-1", AgencyStage.EMPLOYMENT)
    progress = repository.load("subject-1")
    assert progress.current_stage == AgencyStage.CAREER_INTELLIGENCE


def test_marking_the_same_stage_twice_does_not_duplicate(store):
    repository = AgencyCycleProgressRepository(store)
    repository.mark_complete("subject-1", AgencyStage.EMPLOYMENT)
    progress = repository.mark_complete("subject-1", AgencyStage.EMPLOYMENT)
    assert progress.completed_stages.count(AgencyStage.EMPLOYMENT) == 1


def test_is_cycle_complete_only_once_every_stage_is_reached(store):
    repository = AgencyCycleProgressRepository(store)
    for stage in list(AgencyStage)[:-1]:
        repository.mark_complete("subject-1", stage)
    assert repository.load("subject-1").is_cycle_complete is False

    progress = repository.mark_complete("subject-1", AgencyStage.LEARNING)
    assert progress.is_cycle_complete is True
    assert progress.next_stage is None


def test_start_new_cycle_before_completion_raises(store):
    repository = AgencyCycleProgressRepository(store)
    repository.mark_complete("subject-1", AgencyStage.EMPLOYMENT)
    with pytest.raises(CycleNotCompleteError):
        repository.start_new_cycle("subject-1")


def test_start_new_cycle_resets_stages_and_increments_count(store):
    repository = AgencyCycleProgressRepository(store)
    for stage in AgencyStage:
        repository.mark_complete("subject-1", stage)

    progress = repository.start_new_cycle("subject-1")
    assert progress.completed_stages == []
    assert progress.cycles_completed == 1
    assert progress.current_stage is None
    assert progress.next_stage == AgencyStage.EMPLOYMENT


def test_progress_is_scoped_per_subject(store):
    repository = AgencyCycleProgressRepository(store)
    repository.mark_complete("subject-1", AgencyStage.EMPLOYMENT)
    other = repository.load("subject-2")
    assert other.current_stage is None
