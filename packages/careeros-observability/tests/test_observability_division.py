"""Tests for the ObservabilityDivision facade."""

from __future__ import annotations

from careeros_observability import AlertRule, Comparison, ObservabilityDivision
from careeros_trust_layer import FailureQueueRepository, enqueue_failure


def test_metrics_snapshot_reflects_recorded_metrics(store):
    division = ObservabilityDivision(store)
    division.metrics.increment_counter("applications_sent", 3.0)
    snapshot = division.metrics_snapshot()
    assert snapshot.counters["applications_sent"] == 3.0


def test_spans_reflects_traced_work(store):
    division = ObservabilityDivision(store)
    with division.tracer.span("discover_jobs"):
        pass
    names = [span.name for span in division.spans()]
    assert names == ["discover_jobs"]


def test_evaluate_alerts_delegates_to_the_metrics_snapshot(store):
    division = ObservabilityDivision(store)
    division.metrics.set_gauge("queue_depth", 99.0)
    rule = AlertRule(
        name="backed_up",
        metric_name="queue_depth",
        threshold=10.0,
        comparison=Comparison.GREATER_THAN,
    )
    firings = division.evaluate_alerts([rule])
    assert len(firings) == 1
    assert firings[0].rule_name == "backed_up"


def test_explain_pending_failures_reuses_the_trust_layer_failure_queue(store):
    repository = FailureQueueRepository(store)
    enqueue_failure(repository, task_type="job_application", payload={}, error="provider timeout")
    division = ObservabilityDivision(store)
    explanations = division.explain_pending_failures()
    assert len(explanations) == 1
    assert "job_application" in explanations[0]
    assert "provider timeout" in explanations[0]


def test_explain_pending_failures_is_empty_when_queue_is_empty(store):
    division = ObservabilityDivision(store)
    assert division.explain_pending_failures() == []
