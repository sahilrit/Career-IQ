"""Tests for ManualCompanyDiscoveryProvider."""

from __future__ import annotations

from careeros_client_acquisition import (
    Company,
    CompanyDiscoveryQuery,
    ManualCompanyDiscoveryProvider,
)


def _provider():
    return ManualCompanyDiscoveryProvider(
        [
            Company(name="Widget Co", website="https://widgetco.example.com", industry="retail"),
            Company(name="Acme SaaS", website="https://acme.example.com", industry="software"),
        ]
    )


def test_discover_with_no_filters_returns_everything():
    results = _provider().discover(CompanyDiscoveryQuery())
    assert len(results) == 2


def test_discover_filters_by_industry():
    results = _provider().discover(CompanyDiscoveryQuery(industry="software"))
    assert [c.name for c in results] == ["Acme SaaS"]


def test_discover_filters_by_keyword_in_name():
    results = _provider().discover(CompanyDiscoveryQuery(keywords=["widget"]))
    assert [c.name for c in results] == ["Widget Co"]


def test_discover_with_no_matches_returns_empty():
    results = _provider().discover(CompanyDiscoveryQuery(industry="healthcare"))
    assert results == []
