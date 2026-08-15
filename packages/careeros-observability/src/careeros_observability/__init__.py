"""careeros_observability: Observability & Reliability.

Metrics, tracing, threshold alerting, and failure explanation. Health
(Phase 23's PlatformHealthMonitor), dead-letter queues and retries
(Phase 45's failure queue), and plugin/provider monitoring
(Phase 48's health checks) already exist — this fills what those
didn't.
"""

from careeros_observability.alerts import AlertFiring, AlertRule, Comparison, evaluate_alerts
from careeros_observability.exceptions import ObservabilityError
from careeros_observability.failure_explainer import explain_failure, explain_failures
from careeros_observability.metrics import MetricsRegistry, MetricsSnapshot, TimerStats
from careeros_observability.observability_division import ObservabilityDivision
from careeros_observability.tracing import Span, Tracer

__all__ = [
    "AlertFiring",
    "AlertRule",
    "Comparison",
    "MetricsRegistry",
    "MetricsSnapshot",
    "ObservabilityDivision",
    "ObservabilityError",
    "Span",
    "TimerStats",
    "Tracer",
    "evaluate_alerts",
    "explain_failure",
    "explain_failures",
]
