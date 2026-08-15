"""Shared fixtures for CEO agent tests."""

from __future__ import annotations

import pytest

from careeros_ceo_agent import AllocationPlanRepository, PerformanceInputRepository
from careeros_common import DocumentStore


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def performance_repository(store):
    return PerformanceInputRepository(store)


@pytest.fixture
def plan_repository(store):
    return AllocationPlanRepository(store)
