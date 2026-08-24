"""Shared fixtures for billing tests."""

from __future__ import annotations

import pytest

from careeros_billing import SubscriptionRepository
from careeros_billing.open_access import OPEN_ACCESS_ENV_VAR
from careeros_common import DocumentStore


@pytest.fixture(autouse=True)
def tier_enforcement(monkeypatch):
    """Pin open access off for billing tests.

    Open access is on in production right now, which makes every gate
    answer "yes" regardless of tier. These tests are about the plan model
    itself, so they need the override out of the way. ``test_open_access.py``
    sets the variable itself and so overrides this.
    """
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "0")


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def subscription_repository(store):
    return SubscriptionRepository(store)
