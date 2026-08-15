"""Tests for GigPosting/Budget models."""

from __future__ import annotations

from careeros_freelance_providers import Budget


def test_midpoint_averages_min_and_max():
    assert Budget(min_amount=500, max_amount=1500).midpoint() == 1000


def test_midpoint_falls_back_to_min_only():
    assert Budget(min_amount=500).midpoint() == 500


def test_midpoint_falls_back_to_max_only():
    assert Budget(max_amount=1500).midpoint() == 1500


def test_midpoint_is_none_when_no_amounts():
    assert Budget().midpoint() is None


def test_dedupe_key_combines_provider_and_external_id(posting_factory):
    posting = posting_factory(source_provider="fiverr", external_id="42")
    assert posting.dedupe_key == ("fiverr", "42")
