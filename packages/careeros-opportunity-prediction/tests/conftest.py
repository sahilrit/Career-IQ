"""Shared fixtures for opportunity prediction tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_opportunity_prediction import (
    DecisionMakerRepository,
    PredictionProgressRepository,
    PredictionSignalRepository,
)


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def signal_repository(store):
    return PredictionSignalRepository(store)


@pytest.fixture
def decision_maker_repository(store):
    return DecisionMakerRepository(store)


@pytest.fixture
def progress_repository(store):
    return PredictionProgressRepository(store)
