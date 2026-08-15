"""Shared fixtures for offer/negotiation tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_offer_negotiation import Offer, OfferRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def offer_repository(store):
    return OfferRepository(store)


@pytest.fixture
def offer():
    return Offer(
        company_name="Widget Co",
        job_title="Backend Engineer",
        base_salary=150_000,
        bonus=10_000,
        equity_value=20_000,
        benefits_value=15_000,
        pto_days=20,
    )
