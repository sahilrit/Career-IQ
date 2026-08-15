"""Shared fixtures for employment division tests."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_career_brain import Achievement, CareerBrain, Experience, Identity, Project, Skill
from careeros_common import DocumentStore
from careeros_job_providers import JobPosting


def make_brain(**overrides) -> CareerBrain:
    defaults = {
        "identity": Identity(
            full_name="Ada Lovelace", email="ada@example.com", headline="Engineer"
        ),
        "skills": [Skill(name="Python", proficiency=5)],
        "experiences": [
            Experience(
                company_name="Acme",
                title="Backend Engineer",
                start_date=date(2020, 1, 1),
                achievements=[Achievement(description="Shipped a feature", metric="+10% signups")],
            )
        ],
        "projects": [
            Project(name="Open Source Tool", description="A CLI tool", url="https://github.com/x")
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


@pytest.fixture
def posting():
    return JobPosting(
        source_provider="remoteok",
        external_id="1",
        title="Backend Engineer",
        company_name="Widget Co",
        url="https://example.com/1",
        tags=["python"],
    )


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store
