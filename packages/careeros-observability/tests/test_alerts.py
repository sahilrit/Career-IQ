"""Tests for threshold alert evaluation."""

from __future__ import annotations

from careeros_observability import AlertRule, Comparison, MetricsRegistry, evaluate_alerts


def test_greater_than_rule_fires_when_breached():
    registry = MetricsRegistry()
    registry.set_gauge("queue_depth", 42.0)
    rule = AlertRule(
        name="queue_backed_up",
        metric_name="queue_depth",
        threshold=10.0,
        comparison=Comparison.GREATER_THAN,
    )
    firings = evaluate_alerts(registry.snapshot(), [rule])
    assert len(firings) == 1
    assert firings[0].rule_name == "queue_backed_up"
    assert firings[0].observed_value == 42.0
    assert firings[0].threshold == 10.0


def test_greater_than_rule_does_not_fire_when_within_threshold():
    registry = MetricsRegistry()
    registry.set_gauge("queue_depth", 5.0)
    rule = AlertRule(
        name="queue_backed_up",
        metric_name="queue_depth",
        threshold=10.0,
        comparison=Comparison.GREATER_THAN,
    )
    assert evaluate_alerts(registry.snapshot(), [rule]) == []


def test_less_than_rule_fires_when_breached():
    registry = MetricsRegistry()
    registry.set_gauge("success_rate", 0.4)
    rule = AlertRule(
        name="success_rate_dropped",
        metric_name="success_rate",
        threshold=0.5,
        comparison=Comparison.LESS_THAN,
    )
    firings = evaluate_alerts(registry.snapshot(), [rule])
    assert len(firings) == 1
    assert firings[0].observed_value == 0.4


def test_rule_referencing_a_timer_uses_the_mean():
    registry = MetricsRegistry()
    registry.record_timer("apply_duration", 1.0)
    registry.record_timer("apply_duration", 5.0)
    rule = AlertRule(
        name="applies_are_slow",
        metric_name="apply_duration",
        threshold=2.0,
        comparison=Comparison.GREATER_THAN,
    )
    firings = evaluate_alerts(registry.snapshot(), [rule])
    assert len(firings) == 1
    assert firings[0].observed_value == 3.0


def test_rule_referencing_an_unknown_metric_never_fires():
    registry = MetricsRegistry()
    rule = AlertRule(
        name="ghost_metric",
        metric_name="does_not_exist",
        threshold=1.0,
        comparison=Comparison.GREATER_THAN,
    )
    assert evaluate_alerts(registry.snapshot(), [rule]) == []
