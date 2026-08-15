"""Tests for failure explanation."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_observability import explain_failure, explain_failures
from careeros_trust_layer import FailedTask


def test_explain_failure_with_no_retries():
    task = FailedTask(
        task_type="job_application",
        error="timeout contacting provider",
        failed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    explanation = explain_failure(task)
    assert "job_application failed at 2026-01-01T00:00:00+00:00" in explanation
    assert "timeout contacting provider" in explanation
    assert "retried" not in explanation


def test_explain_failure_with_one_retry_uses_singular():
    task = FailedTask(
        task_type="job_application",
        error="timeout",
        retry_count=1,
        failed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert "(retried 1 time)" in explain_failure(task)


def test_explain_failure_with_multiple_retries_uses_plural():
    task = FailedTask(
        task_type="job_application",
        error="timeout",
        retry_count=3,
        failed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert "(retried 3 times)" in explain_failure(task)


def test_explain_failures_maps_over_the_list():
    tasks = [
        FailedTask(task_type="a", error="err_a", failed_at=datetime(2026, 1, 1, tzinfo=UTC)),
        FailedTask(task_type="b", error="err_b", failed_at=datetime(2026, 1, 2, tzinfo=UTC)),
    ]
    explanations = explain_failures(tasks)
    assert len(explanations) == 2
    assert "err_a" in explanations[0]
    assert "err_b" in explanations[1]


def test_explain_failures_of_empty_list_is_empty():
    assert explain_failures([]) == []
