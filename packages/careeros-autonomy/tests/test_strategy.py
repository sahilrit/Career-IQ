"""Sanity checks for the named autonomy strategy presets."""

from __future__ import annotations

from careeros_autonomy import AGGRESSIVE, BALANCED, CONSERVATIVE


def test_presets_are_ordered_from_most_to_least_cautious():
    assert CONSERVATIVE.min_match_score > BALANCED.min_match_score > AGGRESSIVE.min_match_score
    assert (
        CONSERVATIVE.min_seconds_between_actions
        > BALANCED.min_seconds_between_actions
        > AGGRESSIVE.min_seconds_between_actions
    )


def test_presets_have_distinct_names():
    names = {CONSERVATIVE.name, BALANCED.name, AGGRESSIVE.name}
    assert len(names) == 3


def test_presets_are_immutable():
    import dataclasses

    import pytest

    with pytest.raises(dataclasses.FrozenInstanceError):
        BALANCED.min_match_score = 0.1
