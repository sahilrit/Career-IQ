"""Threshold alerting over a metrics snapshot — no external paid
alerting service. A real notifier (Slack, PagerDuty, email) would
consume ``AlertFiring`` records and is deliberately out of scope here,
the same "pluggable, never mandatory" boundary every other integration
in CareerOS respects.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from careeros_observability.metrics import MetricsSnapshot


class Comparison(StrEnum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


class AlertRule(BaseModel):
    name: str
    metric_name: str
    threshold: float
    comparison: Comparison


class AlertFiring(BaseModel):
    rule_name: str
    metric_name: str
    observed_value: float
    threshold: float


def _metric_value(snapshot: MetricsSnapshot, metric_name: str) -> float | None:
    if metric_name in snapshot.counters:
        return snapshot.counters[metric_name]
    if metric_name in snapshot.gauges:
        return snapshot.gauges[metric_name]
    if metric_name in snapshot.timers:
        return snapshot.timers[metric_name].mean_seconds
    return None


def evaluate_alerts(snapshot: MetricsSnapshot, rules: list[AlertRule]) -> list[AlertFiring]:
    firings = []
    for rule in rules:
        value = _metric_value(snapshot, rule.metric_name)
        if value is None:
            continue
        breached = (
            value > rule.threshold
            if rule.comparison == Comparison.GREATER_THAN
            else value < rule.threshold
        )
        if breached:
            firings.append(
                AlertFiring(
                    rule_name=rule.name,
                    metric_name=rule.metric_name,
                    observed_value=value,
                    threshold=rule.threshold,
                )
            )
    return firings
