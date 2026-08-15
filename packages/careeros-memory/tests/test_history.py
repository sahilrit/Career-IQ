"""Tests for HistoryLog."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from careeros_common import DocumentStore
from careeros_memory import HistoryEntry, HistoryLog


@pytest.fixture
def log():
    with DocumentStore() as store:
        yield HistoryLog(store)


def test_append_then_all_returns_the_entry(log):
    log.append(HistoryEntry(category="application", subject_id="app-1", summary="Applied"))
    entries = log.all()
    assert len(entries) == 1
    assert entries[0].summary == "Applied"


def test_for_subject_filters_by_category_and_subject_id(log):
    log.append(HistoryEntry(category="application", subject_id="app-1", summary="Applied"))
    log.append(HistoryEntry(category="application", subject_id="app-2", summary="Applied"))
    log.append(HistoryEntry(category="recruiter", subject_id="app-1", summary="Contacted"))

    entries = log.for_subject("application", "app-1")
    assert [e.summary for e in entries] == ["Applied"]


def test_by_category_returns_only_that_category(log):
    log.append(HistoryEntry(category="application", subject_id="app-1", summary="Applied"))
    log.append(HistoryEntry(category="interview", subject_id="app-1", summary="Scheduled"))

    entries = log.by_category("interview")
    assert [e.summary for e in entries] == ["Scheduled"]


def test_all_is_sorted_by_occurred_at_not_insertion_order():
    with DocumentStore() as store:
        log = HistoryLog(store)
        first = HistoryEntry(
            category="application",
            subject_id="app-1",
            summary="first",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        second = HistoryEntry(
            category="application",
            subject_id="app-1",
            summary="second",
            occurred_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        # Insert out of chronological order to prove sorting, not insertion order.
        log.append(second)
        log.append(first)

        assert [e.summary for e in log.all()] == ["first", "second"]
