"""Tests for parsing ZipRecruiter's embedded JSON-LD job listing data."""

from __future__ import annotations

from careeros_ziprecruiter_provider.parser import (
    extract_ld_json_items,
    has_ld_json_block,
    is_job_entry,
    make_search_url,
    parse_job_entry,
)

# --- URL building --------------------------------------------------------


def test_make_search_url_shape():
    url = make_search_url(keyword="growth marketing", location="New York, NY", page=1)
    assert url.startswith("https://www.ziprecruiter.com/jobs-search?")
    assert "search=growth+marketing" in url
    assert "location=New+York%2C+NY" in url


def test_make_search_url_includes_the_page_number():
    url = make_search_url(keyword="growth", location=None, page=3)
    assert "page=3" in url


def test_make_search_url_omits_location_when_none():
    url = make_search_url(keyword="growth", location=None, page=1)
    assert "location=" not in url


# --- JSON-LD extraction ---------------------------------------------------


def test_extract_ld_json_items_finds_the_item_list(listing_html):
    items = extract_ld_json_items(listing_html)
    assert len(items) == 2
    assert items[0]["name"] == "A"


def test_extract_ld_json_items_handles_html_with_no_script_block():
    assert extract_ld_json_items("<html><body>no data here</body></html>") == []


def test_extract_ld_json_items_handles_malformed_json():
    html = '<script type="application/ld+json">not valid json</script>'
    assert extract_ld_json_items(html) == []


def test_extract_ld_json_items_handles_a_list_with_no_itemlistelement():
    html = '<script type="application/ld+json">{"@type": "ItemList"}</script>'
    assert extract_ld_json_items(html) == []


# --- challenge detection ---------------------------------------------------


def test_has_ld_json_block_is_true_on_a_real_result_page(listing_html):
    assert has_ld_json_block(listing_html) is True


def test_has_ld_json_block_is_false_on_a_challenge_page():
    assert has_ld_json_block("<html><body>Just a moment...</body></html>") is False


# --- item usability --------------------------------------------------------


def test_an_item_without_a_url_is_not_usable(item_unusable):
    assert is_job_entry(item_unusable) is False


def test_an_item_with_a_name_and_url_is_usable(item_full):
    assert is_job_entry(item_full) is True


# --- item -> JobPosting -----------------------------------------------------


def test_parse_maps_the_core_fields(item_full):
    posting = parse_job_entry(item_full)
    assert posting.source_provider == "ziprecruiter"
    assert posting.external_id == "543ce44ea13a0486"
    assert posting.title == "Manager, Business Development - Green Chef"
    assert posting.company_name == "HelloFresh"
    assert posting.url == item_full["url"]


def test_parse_dehyphenates_a_multiword_company_name(item_multiword_company):
    assert parse_job_entry(item_multiword_company).company_name == "AMERICAN MANAGEMENT ASSOC."


def test_parse_dehyphenates_the_location(item_full):
    assert parse_job_entry(item_full).location == "New York, NY"


def test_parse_reads_a_single_word_location(item_multiword_company):
    assert parse_job_entry(item_multiword_company).location == "Manhattan, NY"


def test_remote_location_sets_remote_true():
    item = {
        "name": "X",
        "url": "https://www.ziprecruiter.com/c/Acme/Job/X/-in-Remote?jid=xyz",
    }
    assert parse_job_entry(item).remote is True


def test_a_named_city_is_not_remote(item_full):
    assert parse_job_entry(item_full).remote is False


def test_a_malformed_url_still_parses_without_raising():
    item = {"name": "X", "url": "https://www.ziprecruiter.com/not-the-expected-shape"}
    posting = parse_job_entry(item)
    assert posting.title == "X"
    assert posting.company_name == ""
    assert posting.external_id == ""
