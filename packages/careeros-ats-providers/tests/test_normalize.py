"""Normalization: the shared correctness every adapter depends on."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_ats_providers import (
    annualized_salary,
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)


class TestHtmlToText:
    def test_strips_tags(self):
        assert html_to_text("<p>Hello <b>world</b></p>") == "Hello world"

    def test_decodes_double_encoded_markup(self):
        # Greenhouse ships the body double-encoded. Without decoding BEFORE
        # stripping, "&lt;p&gt;" survives into the description and poisons
        # keyword scoring.
        assert html_to_text("&lt;p&gt;Growth &amp;amp; retention&lt;/p&gt;") == "Growth & retention"

    def test_block_ends_become_line_breaks(self):
        assert html_to_text("<li>One</li><li>Two</li>") == "One\nTwo"

    def test_non_strings_are_empty(self):
        assert html_to_text(None) == "" and html_to_text(42) == "" and html_to_text({}) == ""


class TestToDatetime:
    def test_iso_string(self):
        assert to_datetime("2026-03-04T10:00:00Z") == datetime(2026, 3, 4, 10, 0, tzinfo=UTC)

    def test_naive_iso_is_treated_as_utc(self):
        assert to_datetime("2026-03-04T10:00:00").tzinfo is UTC

    def test_epoch_milliseconds_are_not_read_as_seconds(self):
        # Lever returns ms. Reading them as seconds put every posting ~50,000
        # years in the future and broke recency filtering entirely.
        assert to_datetime(1_741_000_000_000).year == 2025

    def test_epoch_seconds_still_work(self):
        assert to_datetime(1_741_000_000).year == 2025

    def test_unparseable_is_none(self):
        assert to_datetime("last tuesday") is None and to_datetime(None) is None


class TestAnnualizedSalary:
    def test_annual_passes_through(self):
        salary = annualized_salary(100_000, 150_000, "usd", "1 YEAR")
        assert (salary.min_amount, salary.max_amount, salary.currency) == (100_000, 150_000, "USD")

    def test_hourly_is_annualized(self):
        assert annualized_salary(50, 60, "USD", "1 HOUR").min_amount == 104_000

    def test_monthly_is_annualized(self):
        assert annualized_salary(10_000, None, "EUR", "1 MONTH").min_amount == 120_000

    def test_reversed_bounds_are_ordered(self):
        salary = annualized_salary(150_000, 100_000, "USD", "1 YEAR")
        assert salary.min_amount < salary.max_amount

    def test_no_figures_is_none_not_a_zero_salary(self):
        # "No salary given" and "salary of nothing" must stay distinguishable:
        # scoring treats them completely differently.
        assert annualized_salary(None, None, "USD", "1 YEAR") is None
        assert annualized_salary("", "", "USD", "1 YEAR") is None

    def test_unknown_interval_is_none(self):
        assert annualized_salary(100, 200, "USD", "PER FORTNIGHT") is None


class TestLooksRemote:
    def test_detects_remote(self):
        assert looks_remote("Remote - US") and looks_remote("Anywhere")

    def test_hybrid_is_not_remote(self):
        assert not looks_remote("Hybrid - London")

    def test_negations_are_not_remote(self):
        assert not looks_remote("Not remote") and not looks_remote("On-site only")

    def test_ignores_non_strings(self):
        assert not looks_remote(None, 5, {})


class TestMergeLocations:
    def test_dedupes_case_insensitively(self):
        assert merge_locations("London", "london", "Berlin") == "London; Berlin"

    def test_accepts_lists(self):
        assert merge_locations("Hybrid", ["Dublin", "Paris"]) == "Hybrid; Dublin; Paris"

    def test_skips_blanks(self):
        assert merge_locations("", None, "  ", "Oslo") == "Oslo"
