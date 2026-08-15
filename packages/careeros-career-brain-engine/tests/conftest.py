"""Shared fixtures for career brain engine tests."""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, Identity


def make_brain(**overrides) -> CareerBrain:
    defaults = {"identity": Identity(full_name="Ada Lovelace", email="ada@example.com")}
    defaults.update(overrides)
    return CareerBrain(**defaults)


@pytest.fixture
def brain_factory():
    return make_brain
