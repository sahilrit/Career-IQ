"""Shared fixtures for career intelligence tests."""

from __future__ import annotations

import pytest

from careeros_career_intelligence import SignalInputRepository
from careeros_common import DocumentStore


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def signal_repository(store):
    return SignalInputRepository(store)
