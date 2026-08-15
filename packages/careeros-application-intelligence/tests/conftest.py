"""Shared fixtures for application intelligence tests."""

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


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def fake_clock():
    return _FakeClock()
