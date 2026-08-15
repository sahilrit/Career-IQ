"""Tests for OutcomeEvent / OutcomeEventRepository."""

from __future__ import annotations

from careeros_learning_lab import OutcomeEvent, OutcomeType


def test_list_for_variant_filters(outcome_repository):
    matching = OutcomeEvent(variant_id="variant-1", outcome_type=OutcomeType.SENT)
    other = OutcomeEvent(variant_id="variant-2", outcome_type=OutcomeType.SENT)
    outcome_repository.save(matching)
    outcome_repository.save(other)
    assert outcome_repository.list_for_variant("variant-1") == [matching]


def test_default_value_is_one():
    event = OutcomeEvent(variant_id="variant-1", outcome_type=OutcomeType.RESPONSE)
    assert event.value == 1.0
