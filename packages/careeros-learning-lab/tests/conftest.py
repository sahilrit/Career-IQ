"""Shared fixtures for learning lab tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_learning_lab import ExperimentRepository, OutcomeEventRepository, VariantRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def experiment_repository(store):
    return ExperimentRepository(store)


@pytest.fixture
def variant_repository(store):
    return VariantRepository(store)


@pytest.fixture
def outcome_repository(store):
    return OutcomeEventRepository(store)
