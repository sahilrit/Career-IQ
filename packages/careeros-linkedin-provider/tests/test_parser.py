"""Tests for the LinkedIn HTML parsing, against captured markup only."""

from __future__ import annotations

from careeros_linkedin_provider import (
    extract_job_cards,
    is_job_entry,
    parse_description_html,
    parse_job_entry,
)


def test_extract_finds_every_well_formed_card(search_html):
    cards = extract_job_cards(search_html)
    assert len(cards) == 3


def test_a_card_without_a_link_is_not_a_job_entry(search_html):
    cards = extract_job_cards(search_html)
    usable = [card for card in cards if is_job_entry(card)]
    assert len(usable) == 2
    assert all(card["job_id"] for card in usable)


def test_fields_are_pulled_out_and_whitespace_stripped(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4438071583")
    assert card["title"] == "Senior Manager, Performance Marketing"
    assert card["company"] == "Lenskart.com"
    assert card["location"] == "New Delhi, Delhi, India"
    assert card["posted_at"] == "2026-08-04"


def test_tracking_query_string_is_stripped_from_the_url(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4438071583")
    assert "?" not in card["url"]
    assert card["url"].endswith("4438071583")


def test_salary_is_captured_when_present(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4400000001")
    assert card["salary_text"] == "$120,000 - $150,000"


def test_the_new_listdate_class_variant_is_still_read(search_html):
    """LinkedIn uses job-search-card__listdate--new for fresh postings."""
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4400000001")
    assert card["posted_at"] == "2026-08-22"


def test_parse_job_entry_builds_a_posting(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4438071583")
    posting = parse_job_entry(card)
    assert posting.source_provider == "linkedin"
    assert posting.external_id == "4438071583"
    assert posting.title == "Senior Manager, Performance Marketing"
    assert posting.company_name == "Lenskart.com"
    assert posting.posted_at is not None
    assert posting.posted_at.year == 2026


def test_remote_location_sets_the_remote_flag(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4400000001")
    posting = parse_job_entry(card)
    assert posting.remote is True


def test_non_remote_location_leaves_the_flag_off(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4438071583")
    assert parse_job_entry(card).remote is False


def test_salary_range_is_parsed_into_numbers(search_html):
    card = next(c for c in extract_job_cards(search_html) if c.get("job_id") == "4400000001")
    salary = parse_job_entry(card).salary
    assert salary is not None
    assert salary.min_amount == 120000
    assert salary.max_amount == 150000
    assert salary.currency == "USD"


def test_description_html_becomes_readable_text(job_view_html):
    text = parse_description_html(job_view_html)
    assert "Senior Manager, Performance Marketing" in text
    assert "5+ years in paid acquisition" in text
    # Entities decoded, tags gone.
    assert "Google Ads" in text
    assert "SQL & dashboards" in text
    assert "<" not in text


def test_description_returns_empty_when_the_block_is_missing():
    assert parse_description_html("<html><body>nothing here</body></html>") == ""


def test_extract_handles_an_empty_page():
    assert extract_job_cards("\n\n") == []
