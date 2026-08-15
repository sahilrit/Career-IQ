"""Shared fixtures for application engine tests."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_career_brain import Achievement, CareerBrain, Experience, Identity, Skill
from careeros_job_providers import JobPosting


def make_brain(**overrides) -> CareerBrain:
    defaults = {
        "identity": Identity(
            full_name="Ada Lovelace",
            email="ada@example.com",
            headline="Backend Engineer",
            phone="+1-555-0100",
            location="Remote",
        ),
        "skills": [Skill(name="Python", proficiency=5), Skill(name="Django", proficiency=4)],
        "experiences": [
            Experience(
                company_name="Acme",
                title="Senior Backend Engineer",
                start_date=date(2020, 1, 1),
                description="Owned the checkout platform.",
                achievements=[
                    Achievement(
                        description="Rebuilt the Shopify checkout flow", metric="+18% conversion"
                    )
                ],
            )
        ],
    }
    defaults.update(overrides)
    return CareerBrain(**defaults)


def make_posting(**overrides) -> JobPosting:
    defaults = {
        "source_provider": "remoteok",
        "external_id": "1",
        "title": "Senior Python Engineer",
        "company_name": "Widget Co",
        "url": "https://example.com/1",
        "tags": ["python", "django", "shopify"],
        "description": "Own our Shopify integration and checkout flow.",
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


@pytest.fixture
def brain_factory():
    return make_brain


@pytest.fixture
def posting_factory():
    return make_posting


@pytest.fixture
def brain():
    return make_brain()


@pytest.fixture
def posting():
    return make_posting()
