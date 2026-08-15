"""careeros_trust_layer: the Security & Trust Layer.

Tenant isolation (Phase 25), encryption/OAuth/secret management
(Phase 26), and agent authorization (Phase 21) already exist — this
package covers what those didn't: a general-purpose audit log, consent
management, data export/deletion, rate limiting, and a failure queue
with recovery.
"""

from careeros_trust_layer.audit_log import AuditEntry, AuditLogRepository, record_audit_event
from careeros_trust_layer.consent import (
    ConsentRecord,
    ConsentRepository,
    ConsentType,
    grant_consent,
    has_active_consent,
    revoke_consent,
)
from careeros_trust_layer.data_portability import (
    CareerBrainDataDeletor,
    CareerBrainDataExporter,
    DataDeletor,
    DataExporter,
    DataPortabilityRegistry,
)
from careeros_trust_layer.exceptions import TrustLayerError
from careeros_trust_layer.failure_queue import (
    FailedTask,
    FailureQueueRepository,
    FailureStatus,
    enqueue_failure,
    mark_abandoned,
    mark_resolved,
    requeue_for_retry,
)
from careeros_trust_layer.rate_limiter import RateLimiter
from careeros_trust_layer.trust_layer_division import TrustLayerDivision

__all__ = [
    "AuditEntry",
    "AuditLogRepository",
    "CareerBrainDataDeletor",
    "CareerBrainDataExporter",
    "ConsentRecord",
    "ConsentRepository",
    "ConsentType",
    "DataDeletor",
    "DataExporter",
    "DataPortabilityRegistry",
    "FailedTask",
    "FailureQueueRepository",
    "FailureStatus",
    "RateLimiter",
    "TrustLayerDivision",
    "TrustLayerError",
    "enqueue_failure",
    "grant_consent",
    "has_active_consent",
    "mark_abandoned",
    "mark_resolved",
    "record_audit_event",
    "requeue_for_retry",
    "revoke_consent",
]
