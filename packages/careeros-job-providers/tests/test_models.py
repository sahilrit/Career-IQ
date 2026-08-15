"""Tests for JobPosting/Salary models."""

from __future__ import annotations

from careeros_job_providers import Salary


def test_midpoint_averages_min_and_max():
    assert Salary(min_amount=100_000, max_amount=140_000).midpoint() == 120_000


def test_midpoint_falls_back_to_min_only():
    assert Salary(min_amount=100_000).midpoint() == 100_000


def test_midpoint_falls_back_to_max_only():
    assert Salary(max_amount=140_000).midpoint() == 140_000


def test_midpoint_is_none_when_no_amounts():
    assert Salary().midpoint() is None


def test_dedupe_key_combines_provider_and_external_id(posting_factory):
    posting = posting_factory(source_provider="remoteok", external_id="42")
    assert posting.dedupe_key == ("remoteok", "42")
