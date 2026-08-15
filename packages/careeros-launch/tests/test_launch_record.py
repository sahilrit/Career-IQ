"""Tests for LaunchRecordRepository."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_launch import LaunchRecord, LaunchRecordRepository


def test_save_then_list_all(store):
    repository = LaunchRecordRepository(store)
    record = LaunchRecord(version="1.0.0")
    repository.save(record)
    assert repository.list_all() == [record]


def test_latest_returns_the_most_recently_launched(store):
    repository = LaunchRecordRepository(store)
    older = LaunchRecord(version="1.0.0", launched_at=datetime(2026, 1, 1, tzinfo=UTC))
    newer = LaunchRecord(version="1.1.0", launched_at=datetime(2026, 2, 1, tzinfo=UTC))
    repository.save(older)
    repository.save(newer)
    assert repository.latest() == newer


def test_latest_of_empty_repository_is_none(store):
    repository = LaunchRecordRepository(store)
    assert repository.latest() is None
