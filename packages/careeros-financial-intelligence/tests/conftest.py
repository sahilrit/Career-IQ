"""Shared fixtures for financial intelligence tests."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_common import DocumentStore
from careeros_financial_intelligence import IncomeRecord, IncomeRepository, IncomeSource
from careeros_offer_negotiation import Offer, calculate_opportunity_value


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def income_repository(store):
    return IncomeRepository(store)


@pytest.fixture
def salary_record_factory():
    def make(amount: float = 5_000, received_date: date = date(2026, 1, 15), **overrides):
        defaults = {
            "source": IncomeSource.SALARY,
            "source_name": "Acme",
            "amount": amount,
            "received_date": received_date,
        }
        defaults.update(overrides)
        return IncomeRecord(**defaults)

    return make


@pytest.fixture
def full_time_breakdown():
    offer = Offer(company_name="Acme", job_title="Engineer", base_salary=150_000)
    return calculate_opportunity_value(offer)
