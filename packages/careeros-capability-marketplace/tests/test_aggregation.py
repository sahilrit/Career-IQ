"""Tests for the generic result-aggregation helpers."""

from __future__ import annotations

from careeros_capability_marketplace import flatten, flatten_and_dedupe


def test_flatten_combines_sublists_in_order():
    assert flatten([[1, 2], [3], [4, 5]]) == [1, 2, 3, 4, 5]


def test_flatten_with_empty_input_is_empty():
    assert flatten([]) == []


def test_flatten_and_dedupe_keeps_first_occurrence():
    results = [[{"id": "1", "v": "a"}], [{"id": "1", "v": "b"}, {"id": "2", "v": "c"}]]
    deduped = flatten_and_dedupe(results, key=lambda item: item["id"])
    assert deduped == [{"id": "1", "v": "a"}, {"id": "2", "v": "c"}]


def test_flatten_and_dedupe_with_no_duplicates_returns_everything():
    results = [[1, 2], [3, 4]]
    assert flatten_and_dedupe(results, key=lambda item: item) == [1, 2, 3, 4]
