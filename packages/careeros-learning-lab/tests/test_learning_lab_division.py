"""Tests for the LearningLabDivision facade."""

from __future__ import annotations

import pytest

from careeros_learning_lab import (
    Experiment,
    ExperimentType,
    LearningLabDivision,
    OutcomeEvent,
    OutcomeType,
    Variant,
)


@pytest.fixture
def division(experiment_repository, variant_repository, outcome_repository):
    return LearningLabDivision(experiment_repository, variant_repository, outcome_repository)


@pytest.fixture
def experiment(division):
    experiment = Experiment(experiment_type=ExperimentType.EMAIL, name="Subject line test")
    division.create_experiment(experiment)
    return experiment


def _add_outcomes(division, variant_id, *, sent: int, response: int):
    for _ in range(sent):
        division.record_outcome(OutcomeEvent(variant_id=variant_id, outcome_type=OutcomeType.SENT))
    for _ in range(response):
        division.record_outcome(
            OutcomeEvent(variant_id=variant_id, outcome_type=OutcomeType.RESPONSE)
        )


def test_metrics_for_variant_reflects_recorded_outcomes(division, experiment):
    variant = Variant(experiment_id=experiment.id, label="A")
    division.add_variant(variant)
    _add_outcomes(division, variant.id, sent=10, response=3)
    metrics = division.metrics_for_variant(variant.id)
    assert metrics.sent_count == 10
    assert metrics.response_count == 3


def test_metrics_for_experiment_covers_every_variant(division, experiment):
    variant_a = Variant(experiment_id=experiment.id, label="A")
    variant_b = Variant(experiment_id=experiment.id, label="B")
    division.add_variant(variant_a)
    division.add_variant(variant_b)
    _add_outcomes(division, variant_a.id, sent=5, response=1)
    _add_outcomes(division, variant_b.id, sent=5, response=4)
    metrics = division.metrics_for_experiment(experiment.id)
    assert set(metrics) == {variant_a.id, variant_b.id}


def test_winner_for_experiment_picks_the_better_variant(division, experiment):
    variant_a = Variant(experiment_id=experiment.id, label="A")
    variant_b = Variant(experiment_id=experiment.id, label="B")
    division.add_variant(variant_a)
    division.add_variant(variant_b)
    _add_outcomes(division, variant_a.id, sent=10, response=1)
    _add_outcomes(division, variant_b.id, sent=10, response=8)
    assert division.winner_for_experiment(experiment.id) == variant_b.id


def test_winner_for_experiment_with_insufficient_data_is_none(division, experiment):
    variant = Variant(experiment_id=experiment.id, label="A")
    division.add_variant(variant)
    _add_outcomes(division, variant.id, sent=1, response=1)
    assert division.winner_for_experiment(experiment.id) is None
