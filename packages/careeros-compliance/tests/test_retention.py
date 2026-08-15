"""Tests for retention policy evaluation and storage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_compliance import RetentionPolicy, RetentionPolicyRepository, find_expired, is_expired

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_is_expired_when_older_than_retention_window():
    policy = RetentionPolicy(entity_type="audit_entry", retention_days=30)
    created_at = _NOW - timedelta(days=31)
    assert is_expired(created_at, policy, now=_NOW) is True


def test_is_not_expired_when_within_retention_window():
    policy = RetentionPolicy(entity_type="audit_entry", retention_days=30)
    created_at = _NOW - timedelta(days=10)
    assert is_expired(created_at, policy, now=_NOW) is False


def test_is_expired_at_exact_boundary():
    policy = RetentionPolicy(entity_type="audit_entry", retention_days=30)
    created_at = _NOW - timedelta(days=30)
    assert is_expired(created_at, policy, now=_NOW) is True


def test_find_expired_returns_only_overdue_ids():
    policy = RetentionPolicy(entity_type="audit_entry", retention_days=30)
    records = {
        "old": _NOW - timedelta(days=60),
        "fresh": _NOW - timedelta(days=5),
    }
    assert find_expired(records, policy, now=_NOW) == ["old"]


def test_retention_policy_repository_round_trips(store):
    repository = RetentionPolicyRepository(store)
    policy = RetentionPolicy(entity_type="audit_entry", retention_days=90)
    repository.save(policy)
    loaded = repository.load("audit_entry")
    assert loaded == policy


def test_retention_policy_repository_load_missing_returns_none(store):
    repository = RetentionPolicyRepository(store)
    assert repository.load("does_not_exist") is None


def test_retention_policy_repository_list_all(store):
    repository = RetentionPolicyRepository(store)
    repository.save(RetentionPolicy(entity_type="audit_entry", retention_days=90))
    repository.save(RetentionPolicy(entity_type="consent_record", retention_days=365))
    assert len(repository.list_all()) == 2
