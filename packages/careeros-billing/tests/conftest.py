"""Shared fixtures for billing tests."""

from __future__ import annotations

import pytest

from careeros_billing import SubscriptionRepository
from careeros_common import DocumentStore


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def subscription_repository(store):
    return SubscriptionRepository(store)
