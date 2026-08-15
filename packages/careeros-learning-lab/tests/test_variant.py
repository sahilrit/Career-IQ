"""Tests for Variant / VariantRepository."""

from __future__ import annotations

from careeros_learning_lab import Variant


def test_list_for_experiment_filters(variant_repository):
    matching = Variant(experiment_id="experiment-1", label="A", content="Version A")
    other = Variant(experiment_id="experiment-2", label="A", content="Unrelated")
    variant_repository.save(matching)
    variant_repository.save(other)
    assert variant_repository.list_for_experiment("experiment-1") == [matching]


def test_load_returns_saved_variant(variant_repository):
    variant = Variant(experiment_id="experiment-1", label="B", content="Version B")
    variant_repository.save(variant)
    assert variant_repository.load(variant.id) == variant
