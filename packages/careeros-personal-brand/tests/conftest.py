"""Shared fixtures for personal brand tests."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_career_brain import Achievement, CareerBrain, Experience, Identity, Project, Skill
from careeros_common import DocumentStore
from careeros_personal_brand import ContentProgressRepository, TestimonialRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def progress_repository(store):
    return ContentProgressRepository(store)


@pytest.fixture
def testimonial_repository(store):
    return TestimonialRepository(store)


@pytest.fixture
def project():
    return Project(
        name="Open Source Tool",
        description="A CLI tool that automates release notes.",
        url="https://github.com/x/tool",
        skills_used=["Python", "CLI design"],
    )


@pytest.fixture
def brain(project):
    return CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com", headline="Engineer"),
        skills=[Skill(name="Python", proficiency=5)],
        experiences=[
            Experience(
                company_name="Acme",
                title="Backend Engineer",
                start_date=date(2020, 1, 1),
                achievements=[
                    Achievement(
                        description="Automated the release notes tool for every repo",
                        metric="saved 3 hours/week",
                    )
                ],
            )
        ],
        projects=[project],
    )
