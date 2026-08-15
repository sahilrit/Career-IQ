"""Shared fixtures for onboarding tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_onboarding import OnboardingProgressRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def progress_repository(store):
    return OnboardingProgressRepository(store)
