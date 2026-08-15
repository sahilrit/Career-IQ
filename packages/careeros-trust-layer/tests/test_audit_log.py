"""Tests for AuditLogRepository / record_audit_event."""

from __future__ import annotations

from careeros_trust_layer import AuditLogRepository, record_audit_event


def test_record_audit_event_persists(store):
    repository = AuditLogRepository(store)
    entry = record_audit_event(
        repository,
        actor_id="user-1",
        action="view",
        resource_type="career_brain",
        resource_id="brain-1",
    )
    assert repository.list_all() == [entry]


def test_list_for_resource_filters(store):
    repository = AuditLogRepository(store)
    record_audit_event(
        repository, actor_id="user-1", action="view", resource_type="offer", resource_id="offer-1"
    )
    record_audit_event(
        repository, actor_id="user-1", action="view", resource_type="offer", resource_id="offer-2"
    )
    entries = repository.list_for_resource("offer", "offer-1")
    assert len(entries) == 1
    assert entries[0].resource_id == "offer-1"


def test_list_for_actor_filters(store):
    repository = AuditLogRepository(store)
    record_audit_event(
        repository, actor_id="user-1", action="view", resource_type="offer", resource_id="offer-1"
    )
    record_audit_event(
        repository, actor_id="user-2", action="view", resource_type="offer", resource_id="offer-2"
    )
    entries = repository.list_for_actor("user-1")
    assert len(entries) == 1
    assert entries[0].actor_id == "user-1"


def test_metadata_defaults_to_empty_dict(store):
    repository = AuditLogRepository(store)
    entry = record_audit_event(
        repository, actor_id="user-1", action="view", resource_type="offer", resource_id="offer-1"
    )
    assert entry.metadata == {}
