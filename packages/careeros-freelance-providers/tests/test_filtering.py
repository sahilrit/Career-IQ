"""Tests for filter_postings/matches_query."""

from __future__ import annotations

from careeros_freelance_providers import Budget, GigSearchQuery, ProjectType, matches_query


def test_min_budget_excludes_postings_below_threshold(posting_factory):
    posting = posting_factory(budget=Budget(min_amount=200, max_amount=300))
    assert not matches_query(posting, GigSearchQuery(min_budget=500))


def test_min_budget_excludes_postings_with_no_budget_listed(posting_factory):
    posting = posting_factory(budget=None)
    assert not matches_query(posting, GigSearchQuery(min_budget=500))


def test_min_budget_includes_postings_at_or_above_threshold(posting_factory):
    posting = posting_factory(budget=Budget(min_amount=500, max_amount=800))
    assert matches_query(posting, GigSearchQuery(min_budget=500))


def test_project_type_filter(posting_factory):
    hourly = posting_factory(budget=Budget(project_type=ProjectType.HOURLY))
    assert matches_query(hourly, GigSearchQuery(project_types=[ProjectType.HOURLY]))
    assert not matches_query(hourly, GigSearchQuery(project_types=[ProjectType.FIXED_PRICE]))


def test_skills_filter_matches_any_overlap(posting_factory):
    posting = posting_factory(skills_required=["Shopify", "CRO"])
    assert matches_query(posting, GigSearchQuery(skills=["shopify"]))
    assert not matches_query(posting, GigSearchQuery(skills=["wordpress"]))


def test_keyword_filter_matches_title_or_description(posting_factory):
    posting = posting_factory(title="Shopify Store Redesign", description="Improve conversion rate")
    assert matches_query(posting, GigSearchQuery(keywords=["shopify"]))
    assert matches_query(posting, GigSearchQuery(keywords=["conversion"]))
    assert not matches_query(posting, GigSearchQuery(keywords=["wordpress"]))


def test_empty_query_matches_everything(posting_factory):
    posting = posting_factory()
    assert matches_query(posting, GigSearchQuery())
