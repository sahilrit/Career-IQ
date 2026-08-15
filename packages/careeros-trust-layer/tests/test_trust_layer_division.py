"""Tests for the TrustLayerDivision facade."""

from __future__ import annotations

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_trust_layer import ConsentType, RateLimiter, TrustLayerDivision


def test_record_and_read_audit_trail(store):
    division = TrustLayerDivision(store)
    division.record_audit_event(
        actor_id="user-1", action="view", resource_type="offer", resource_id="offer-1"
    )
    assert len(division.audit_trail_for("offer", "offer-1")) == 1


def test_consent_round_trip(store):
    division = TrustLayerDivision(store)
    division.grant_consent("user-1", ConsentType.DATA_PROCESSING)
    assert division.has_active_consent("user-1", ConsentType.DATA_PROCESSING) is True
    division.revoke_consent("user-1", ConsentType.DATA_PROCESSING)
    assert division.has_active_consent("user-1", ConsentType.DATA_PROCESSING) is False


def test_rate_limit_delegates_to_the_configured_limiter(store):
    limiter = RateLimiter(max_actions=1, window_seconds=60)
    division = TrustLayerDivision(store, rate_limiter=limiter)
    assert division.try_acquire_rate_limit("user-1") is True
    assert division.try_acquire_rate_limit("user-1") is False


def test_failure_queue_lifecycle(store):
    division = TrustLayerDivision(store)
    task = division.enqueue_failure(task_type="apply", payload={}, error="boom")
    assert division.pending_failures() == [task]
    division.resolve_failure(task.id)
    assert division.pending_failures() == []
    retried = division.retry_failure(task.id)
    assert retried.retry_count == 1
    assert division.pending_failures() == [retried]


def test_career_brain_export_and_delete_are_wired_by_default(store):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    division = TrustLayerDivision(store)

    exported = division.export_user_data(brain.identity.id)
    assert "career_brain" in exported

    results = division.delete_user_data(brain.identity.id)
    assert results["career_brain"] is True
    assert CareerBrainRepository(store).load_or_none(brain.identity.id) is None
