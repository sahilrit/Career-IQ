"""Shared fixtures for application runner tests."""

from __future__ import annotations

import pytest

from careeros_application_engine import build_application_package
from careeros_browser import FakeBrowserSession
from careeros_career_brain import CareerBrain, Identity
from careeros_job_providers import JobPosting


@pytest.fixture
def session():
    return FakeBrowserSession()


@pytest.fixture
def package():
    brain = CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com", phone="+1-555-0100")
    )
    posting = JobPosting(
        source_provider="remoteok",
        external_id="1",
        title="Backend Engineer",
        company_name="Acme",
        url="https://example.com/1",
    )
    return build_application_package(brain, posting)
