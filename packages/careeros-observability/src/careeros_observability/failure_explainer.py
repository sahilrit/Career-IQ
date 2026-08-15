"""Explains a failure in plain language — reuses Phase 45's
FailedTask/FailureQueueRepository rather than a second failure-tracking
mechanism; this module is purely about turning that record into
something a human (or an alert) can read.
"""

from __future__ import annotations

from careeros_trust_layer import FailedTask


def explain_failure(task: FailedTask) -> str:
    retry_note = (
        f" (retried {task.retry_count} time{'s' if task.retry_count != 1 else ''})"
        if task.retry_count
        else ""
    )
    return f"{task.task_type} failed at {task.failed_at.isoformat()}{retry_note}: {task.error}"


def explain_failures(tasks: list[FailedTask]) -> list[str]:
    return [explain_failure(task) for task in tasks]
