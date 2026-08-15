"""Tests for PipelineProgress / PipelineProgressRepository."""

from __future__ import annotations

import pytest

from careeros_employment_division import PipelineProgressRepository, PipelineStage


@pytest.fixture
def repository(store):
    return PipelineProgressRepository(store)


def test_fresh_progress_has_no_current_stage(repository):
    progress = repository.load("app-1")
    assert progress.current_stage is None
    assert progress.next_stage == PipelineStage.DISCOVERY


def test_marking_a_stage_complete_updates_current_and_next(repository):
    repository.mark_complete("app-1", PipelineStage.DISCOVERY)
    progress = repository.load("app-1")
    assert progress.current_stage == PipelineStage.DISCOVERY
    assert progress.next_stage == PipelineStage.SCORING


def test_current_stage_is_the_furthest_reached_regardless_of_marking_order(repository):
    repository.mark_complete("app-1", PipelineStage.RESUME)
    repository.mark_complete("app-1", PipelineStage.DISCOVERY)
    progress = repository.load("app-1")
    assert progress.current_stage == PipelineStage.RESUME


def test_marking_the_same_stage_twice_does_not_duplicate(repository):
    repository.mark_complete("app-1", PipelineStage.DISCOVERY)
    repository.mark_complete("app-1", PipelineStage.DISCOVERY)
    progress = repository.load("app-1")
    assert progress.completed_stages.count(PipelineStage.DISCOVERY) == 1


def test_final_stage_has_no_next_stage(repository):
    repository.mark_complete("app-1", PipelineStage.NEGOTIATION)
    progress = repository.load("app-1")
    assert progress.next_stage is None


def test_progress_is_isolated_per_application(repository):
    repository.mark_complete("app-1", PipelineStage.DISCOVERY)
    other = repository.load("app-2")
    assert other.current_stage is None
