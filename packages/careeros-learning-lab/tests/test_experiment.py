"""Tests for Experiment / ExperimentRepository."""

from __future__ import annotations

from careeros_learning_lab import Experiment, ExperimentType


def test_save_and_load_round_trips(experiment_repository):
    experiment = Experiment(experiment_type=ExperimentType.RESUME, name="Resume headline test")
    experiment_repository.save(experiment)
    assert experiment_repository.load(experiment.id) == experiment


def test_list_all_returns_every_saved_experiment(experiment_repository):
    experiment = Experiment(experiment_type=ExperimentType.EMAIL, name="Subject line test")
    experiment_repository.save(experiment)
    assert experiment_repository.list_all() == [experiment]
