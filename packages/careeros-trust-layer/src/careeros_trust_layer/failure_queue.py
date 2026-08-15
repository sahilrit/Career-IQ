"""Failure queue: a dead-letter queue for background work that failed —
the Runtime (Phase 9) has nowhere today to put a job that errored out
beyond a log line. Recording it here makes failures visible and
retriable instead of silently lost.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "failed_task"


class FailureStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class FailedTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str
    payload: dict = Field(default_factory=dict)
    error: str
    status: FailureStatus = FailureStatus.PENDING
    retry_count: int = 0
    failed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FailureQueueRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, task: FailedTask) -> None:
        self._store.put(_ENTITY_TYPE, task.id, task.model_dump(mode="json"))

    def load(self, task_id: str) -> FailedTask:
        return FailedTask.model_validate(self._store.get(_ENTITY_TYPE, task_id))

    def list_all(self) -> list[FailedTask]:
        return [FailedTask.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_pending(self) -> list[FailedTask]:
        return [task for task in self.list_all() if task.status == FailureStatus.PENDING]


def enqueue_failure(
    repository: FailureQueueRepository, *, task_type: str, payload: dict, error: str
) -> FailedTask:
    task = FailedTask(task_type=task_type, payload=payload, error=error)
    repository.save(task)
    return task


def mark_resolved(repository: FailureQueueRepository, task_id: str) -> FailedTask:
    task = repository.load(task_id)
    task.status = FailureStatus.RESOLVED
    repository.save(task)
    return task


def mark_abandoned(repository: FailureQueueRepository, task_id: str) -> FailedTask:
    task = repository.load(task_id)
    task.status = FailureStatus.ABANDONED
    repository.save(task)
    return task


def requeue_for_retry(repository: FailureQueueRepository, task_id: str) -> FailedTask:
    """Recovery: bumps retry_count and puts the task back to PENDING."""
    task = repository.load(task_id)
    task.retry_count += 1
    task.status = FailureStatus.PENDING
    repository.save(task)
    return task
