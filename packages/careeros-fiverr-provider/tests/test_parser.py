"""Tests for Fiverr gig-card entry parsing."""

from __future__ import annotations

from careeros_fiverr_provider import parse_listing


def test_parses_core_fields():
    posting = parse_listing(
        {
            "title": "I will redesign your Shopify storefront",
            "seller": "ada_dev",
            "price": "$1,250",
            "url": "https://www.fiverr.com/ada_dev/redesign-shopify-storefront",
        }
    )
    assert posting is not None
    assert posting.source_provider == "fiverr"
    assert posting.title == "I will redesign your Shopify storefront"
    assert posting.client_name == "ada_dev"
    assert posting.external_id == "redesign-shopify-storefront"


def test_parses_price_into_a_budget():
    posting = parse_listing(
        {"title": "Gig", "seller": "x", "price": "$1,250", "url": "https://x.example/1"}
    )
    assert posting.budget.min_amount == 1250
    assert posting.budget.max_amount == 1250


def test_missing_price_yields_no_budget():
    posting = parse_listing({"title": "Gig", "seller": "x", "url": "https://x.example/1"})
    assert posting.budget is None


def test_missing_title_returns_none():
    assert parse_listing({"seller": "x", "url": "https://x.example/1"}) is None


def test_missing_url_returns_none():
    assert parse_listing({"title": "Gig", "seller": "x"}) is None


def test_missing_seller_falls_back_to_placeholder():
    posting = parse_listing({"title": "Gig", "url": "https://x.example/1"})
    assert posting.client_name == "Unknown seller"
