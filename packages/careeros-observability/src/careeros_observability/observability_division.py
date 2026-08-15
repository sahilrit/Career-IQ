"""ObservabilityDivision: the facade tying metrics, tracing, alerting,
and failure explanation together — reusing Phase 45's failure queue
for pending failures rather than a second dead-letter mechanism.
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_observability.alerts import AlertFiring, AlertRule, evaluate_alerts
from careeros_observability.failure_explainer import explain_failures
from careeros_observability.metrics import MetricsRegistry, MetricsSnapshot
from careeros_observability.tracing import Span, Tracer
from careeros_trust_layer import FailureQueueRepository


class ObservabilityDivision:
    def __init__(self, store: DocumentStore) -> None:
        self.metrics = MetricsRegistry()
        self.tracer = Tracer()
        self._failures = FailureQueueRepository(store)

    def metrics_snapshot(self) -> MetricsSnapshot:
        return self.metrics.snapshot()

    def spans(self) -> list[Span]:
        return self.tracer.spans()

    def evaluate_alerts(self, rules: list[AlertRule]) -> list[AlertFiring]:
        return evaluate_alerts(self.metrics.snapshot(), rules)

    def explain_pending_failures(self) -> list[str]:
        return explain_failures(self._failures.list_pending())
