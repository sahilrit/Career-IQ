"""Tests for ManualCompanyResearchProvider."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_interview_intelligence import CompanyResearch, ManualCompanyResearchProvider


@pytest.fixture
def provider():
    with DocumentStore() as store:
        yield ManualCompanyResearchProvider(store)


def test_get_returns_none_when_nothing_saved(provider):
    assert provider.get("event-1") is None


def test_save_then_get_roundtrips(provider):
    research = CompanyResearch(
        calendar_event_id="event-1", company_name="Acme", business_model="B2B SaaS"
    )
    provider.save(research)
    loaded = provider.get("event-1")
    assert loaded is not None
    assert loaded.business_model == "B2B SaaS"


def test_fields_default_to_empty_not_fabricated():
    research = CompanyResearch(calendar_event_id="event-1")
    assert research.business_model == ""
    assert research.products == []
    assert research.competitors == []
