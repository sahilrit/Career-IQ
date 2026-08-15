"""Tests for deduplicate()."""

from __future__ import annotations

from careeros_freelance_providers import deduplicate


def test_keeps_first_occurrence_of_duplicate_key(posting_factory):
    first = posting_factory(source_provider="fiverr", external_id="1", title="First seen")
    duplicate = posting_factory(source_provider="fiverr", external_id="1", title="Duplicate")
    result = deduplicate([first, duplicate])
    assert len(result) == 1
    assert result[0].title == "First seen"


def test_different_providers_with_same_external_id_are_not_duplicates(posting_factory):
    a = posting_factory(source_provider="fiverr", external_id="1")
    b = posting_factory(source_provider="upwork", external_id="1")
    assert len(deduplicate([a, b])) == 2


def test_empty_list_returns_empty_list():
    assert deduplicate([]) == []
