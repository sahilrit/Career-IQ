"""Tests for parsing one Gradcracker job-card's outer HTML."""

from __future__ import annotations

from careeros_gradcracker_provider.parser import (
    is_job_entry,
    make_search_url,
    parse_article,
)

# --- URL building --------------------------------------------------------


def test_make_search_url_builds_the_role_and_region_path():
    url = make_search_url(role="web-development", region="yorkshire")
    assert url == (
        "https://www.gradcracker.com/search/computing-technology/"
        "web-development-graduate-jobs-in-yorkshire?order=dateAdded"
    )


def test_make_search_url_slugifies_a_free_text_role():
    url = make_search_url(role="Software Systems Engineer", region="north-west")
    assert "software-systems-engineer-graduate-jobs-in-north-west" in url


# --- article parsing -------------------------------------------------------


def test_a_card_without_a_link_is_not_usable(article_no_link):
    assert is_job_entry(article_no_link) is False


def test_a_card_with_a_link_is_usable(article_full):
    assert is_job_entry(article_full) is True


def test_parse_reads_the_title_and_url(article_full):
    posting = parse_article(article_full)
    assert posting is not None
    assert posting.title == "Software Engineering Graduate Scheme"
    assert posting.url == (
        "https://www.gradcracker.com/jobs/software-engineering-graduate-scheme-acme-441122"
    )


def test_parse_reads_the_employer_from_the_figure_alt_text(article_full):
    assert parse_article(article_full).company_name == "Acme Engineering"


def test_parse_reads_the_location_dd(article_full):
    assert parse_article(article_full).location == "Leeds, Yorkshire"


def test_parse_reads_a_numeric_salary_range(article_full):
    salary = parse_article(article_full).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency) == (28000, 32000, "GBP")


def test_a_non_numeric_salary_is_dropped_not_fabricated(article_competitive_salary):
    """Gradcracker's salary field is often "Competitive" rather than a
    figure — matching the Adzuna/LinkedIn precedent, an unparseable value is
    dropped rather than guessed at."""
    assert parse_article(article_competitive_salary).salary is None


def test_a_missing_salary_dd_is_also_none(article_minimal):
    assert parse_article(article_minimal).salary is None


def test_parse_reads_disciplines_as_tags(article_full):
    tags = parse_article(article_full).tags
    assert "software engineering" in tags
    assert "web development" in tags


def test_parse_includes_the_deadline_and_degree_in_the_description(article_full):
    description = parse_article(article_full).description
    assert "30th September 2026" in description
    assert "2:1" in description


def test_a_minimal_card_still_parses(article_minimal):
    posting = parse_article(article_minimal)
    assert posting is not None
    assert posting.title == "Remote Graduate Developer"
    assert posting.salary is None


def test_remote_location_sets_the_remote_flag(article_minimal):
    assert parse_article(article_minimal).remote is True


def test_a_city_location_is_not_remote(article_full):
    assert parse_article(article_full).remote is False


def test_parse_article_returns_none_for_an_unusable_card(article_no_link):
    assert parse_article(article_no_link) is None


def test_parse_never_raises_on_empty_html():
    assert parse_article("") is None


def test_parse_never_raises_on_malformed_html():
    assert parse_article("<article wire:key='x'><h2><a href=") is None
