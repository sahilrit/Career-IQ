"""Tests for parsing a Glassdoor search-results job card."""

from __future__ import annotations

from careeros_glassdoor_provider.parser import (
    has_listing_marker,
    is_job_entry,
    make_search_url,
    parse_card,
)

# --- URL building --------------------------------------------------------


def test_make_search_url_shape():
    url = make_search_url(keyword="growth marketing", page=1)
    assert url.startswith("https://www.glassdoor.com/Job/jobs.htm?")
    assert "sc.keyword=growth+marketing" in url


def test_make_search_url_includes_the_page_number():
    url = make_search_url(keyword="growth", page=3)
    assert "p=3" in url


# --- card usability ---------------------------------------------------------


def test_a_card_without_a_title_link_is_not_usable(card_unusable):
    assert is_job_entry(card_unusable) is False


def test_a_card_with_a_title_link_is_usable(card_with_salary):
    assert is_job_entry(card_with_salary) is True


# --- card -> JobPosting ------------------------------------------------------


def test_parse_maps_the_core_fields(card_with_salary):
    posting = parse_card(card_with_salary)
    assert posting is not None
    assert posting.source_provider == "glassdoor"
    assert posting.external_id == "1010229431335"
    assert posting.title == "Senior Marketing Specialist"
    assert posting.company_name == "Dow"
    assert "1010229431335" in posting.url


def test_parse_reads_the_location(card_with_salary):
    assert parse_card(card_with_salary).location == "Navi Mumbai"


def test_remote_location_sets_remote_true(card_without_salary):
    assert parse_card(card_without_salary).remote is True


def test_a_named_city_is_not_remote(card_with_salary):
    assert parse_card(card_with_salary).remote is False


def test_parse_reads_an_inr_lakh_salary_range(card_with_salary):
    salary = parse_card(card_with_salary).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency) == (500_000, 800_000, "INR")


def test_a_card_without_a_salary_block_has_no_salary(card_without_salary):
    assert parse_card(card_without_salary).salary is None


def test_parse_reads_the_description(card_with_salary):
    assert "global teams" in parse_card(card_with_salary).description


def test_a_card_without_a_description_block_still_parses(card_without_salary):
    posting = parse_card(card_without_salary)
    assert posting is not None
    assert posting.description == ""


def test_a_card_missing_the_title_link_returns_none(card_unusable):
    assert parse_card(card_unusable) is None


# --- bot-wall detection -----------------------------------------------------


def test_has_listing_marker_is_true_on_a_real_results_page():
    assert has_listing_marker('{"@context":"https://schema.org","@type":"ItemList"}') is True


def test_has_listing_marker_is_false_on_a_blocked_page():
    assert has_listing_marker("<html><body>Security | Glassdoor</body></html>") is False


def test_a_dollar_k_salary_parses():
    card = (
        '<div data-test="job-card-wrapper">'
        '<span class="EmployerProfile_compactEmployerName__x">Acme</span>'
        '<a data-test="job-title" href="https://www.glassdoor.com/x.htm?jl=99" '
        'id="job-title-99">Role</a>'
        '<div data-test="detailSalary" id="job-salary-99">$50K - $70K (Employer est.)</div>'
        "</div>"
    )
    salary = parse_card(card).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency) == (50_000, 70_000, "USD")
