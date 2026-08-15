"""Shared fixtures for interview intelligence tests."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_career_brain import Achievement, CareerBrain, Experience, Identity, Skill


def make_brain(**overrides) -> CareerBrain:
    defaults = {
        "identity": Identity(full_name="Ada Lovelace", email="ada@example.com"),
        "skills": [
            Skill(name="Python", proficiency=5),
            Skill(name="Django", proficiency=4),
            Skill(name="SQL", proficiency=3),
        ],
        "experiences": [
            Experience(
                company_name="Acme",
                title="Senior Backend Engineer",
                start_date=date(2020, 1, 1),
                achievements=[
                    Achievement(
                        description="Rebuilt the Shopify checkout flow",
                        metric="+18% conversion",
                    )
                ],
            )
        ],
    }
    defaults.update(overrides)
    return CareerBrain(**defaults)


@pytest.fixture
def brain_factory():
    return make_brain


@pytest.fixture
def brain():
    return make_brain()
