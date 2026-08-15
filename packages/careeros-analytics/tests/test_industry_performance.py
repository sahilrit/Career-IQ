"""Tests for compute_industry_performance."""

from __future__ import annotations

from careeros_analytics import compute_industry_performance
from careeros_client_acquisition import Company


def test_groups_by_industry():
    companies = [
        Company(name="A", website="https://a.example.com", industry="retail"),
        Company(name="B", website="https://b.example.com", industry="retail"),
        Company(name="C", website="https://c.example.com", industry="software"),
    ]
    counts = compute_industry_performance(companies)
    assert counts == {"retail": 2, "software": 1}


def test_missing_industry_groups_under_unknown():
    companies = [Company(name="A", website="https://a.example.com")]
    assert compute_industry_performance(companies) == {"unknown": 1}
