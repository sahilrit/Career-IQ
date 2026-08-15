"""Shared fixtures for skill marketplace tests."""

from __future__ import annotations

import pytest

from careeros_skill_marketplace import SEED_SKILLS


@pytest.fixture
def skills():
    return list(SEED_SKILLS)
