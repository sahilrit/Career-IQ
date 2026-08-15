"""Tests for BrowserFiverrTransport, entirely against FakeBrowserSession."""

from __future__ import annotations

from careeros_browser import FakeBrowserSession
from careeros_fiverr_provider import BrowserFiverrTransport, FiverrSelectors
from careeros_freelance_providers import GigSearchQuery


def test_navigates_to_a_search_url_built_from_the_query():
    session = FakeBrowserSession()
    transport = BrowserFiverrTransport(session)

    transport.fetch_listings(GigSearchQuery(keywords=["shopify", "cro"]))

    assert "fiverr.com/search/gigs" in session.current_url
    assert "shopify" in session.current_url


def test_falls_back_to_skills_when_no_keywords():
    session = FakeBrowserSession()
    transport = BrowserFiverrTransport(session)

    transport.fetch_listings(GigSearchQuery(skills=["wordpress"]))

    assert "wordpress" in session.current_url


def test_extracts_queued_listings_using_the_configured_selectors():
    session = FakeBrowserSession()
    selectors = FiverrSelectors()
    session.set_query_all_results(
        selectors.listing_selector,
        [{"title": "Shopify redesign", "seller": "ada_dev", "price": "$500", "url": "https://x/1"}],
    )
    transport = BrowserFiverrTransport(session, selectors=selectors)

    entries = transport.fetch_listings(GigSearchQuery())

    assert entries == [
        {"title": "Shopify redesign", "seller": "ada_dev", "price": "$500", "url": "https://x/1"}
    ]


def test_custom_selectors_are_honored():
    session = FakeBrowserSession()
    custom = FiverrSelectors(listing_selector=".custom-card")
    session.set_query_all_results(".custom-card", [{"title": "Gig", "url": "https://x/1"}])
    transport = BrowserFiverrTransport(session, selectors=custom)

    entries = transport.fetch_listings(GigSearchQuery())

    assert entries == [{"title": "Gig", "url": "https://x/1"}]
