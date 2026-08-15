"""Tests for the failure queue and recovery."""

from __future__ import annotations

from careeros_trust_layer import (
    FailureQueueRepository,
    FailureStatus,
    enqueue_failure,
    mark_abandoned,
    mark_resolved,
    requeue_for_retry,
)


def test_enqueue_failure_is_pending(store):
    repository = FailureQueueRepository(store)
    task = enqueue_failure(repository, task_type="apply", payload={"job_id": "1"}, error="boom")
    assert task.status == FailureStatus.PENDING
    assert repository.list_pending() == [task]


def test_mark_resolved_removes_it_from_pending(store):
    repository = FailureQueueRepository(store)
    task = enqueue_failure(repository, task_type="apply", payload={}, error="boom")
    mark_resolved(repository, task.id)
    assert repository.list_pending() == []


def test_mark_abandoned_removes_it_from_pending(store):
    repository = FailureQueueRepository(store)
    task = enqueue_failure(repository, task_type="apply", payload={}, error="boom")
    mark_abandoned(repository, task.id)
    assert repository.list_pending() == []


def test_requeue_for_retry_increments_retry_count_and_reopens(store):
    repository = FailureQueueRepository(store)
    task = enqueue_failure(repository, task_type="apply", payload={}, error="boom")
    mark_resolved(repository, task.id)
    retried = requeue_for_retry(repository, task.id)
    assert retried.retry_count == 1
    assert retried.status == FailureStatus.PENDING
    assert repository.list_pending() == [retried]
