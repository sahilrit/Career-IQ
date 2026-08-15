"""TrustLayerDivision: the facade tying the audit log, consent
records, rate limiting, the failure queue, and data portability
together. Tenant isolation, encryption, OAuth, secret management, and
agent authorization are Phase 25/26/21's job, not duplicated here —
this covers what those phases didn't.
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_trust_layer.audit_log import AuditEntry, AuditLogRepository, record_audit_event
from careeros_trust_layer.consent import (
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
from careeros_trust_layer.failure_queue import (
    FailedTask,
    FailureQueueRepository,
    enqueue_failure,
    mark_resolved,
    requeue_for_retry,
)
from careeros_trust_layer.rate_limiter import RateLimiter


class TrustLayerDivision:
    def __init__(self, store: DocumentStore, *, rate_limiter: RateLimiter | None = None) -> None:
        self._store = store
        self._audit_log = AuditLogRepository(store)
        self._consent = ConsentRepository(store)
        self._failures = FailureQueueRepository(store)
        self._rate_limiter = rate_limiter or RateLimiter(max_actions=60, window_seconds=60)
        self._portability = DataPortabilityRegistry()
        self._portability.register_exporter("career_brain", CareerBrainDataExporter(store))
        self._portability.register_deletor("career_brain", CareerBrainDataDeletor(store))

    def record_audit_event(
        self,
        *,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        tenant_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditEntry:
        return record_audit_event(
            self._audit_log,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            metadata=metadata,
        )

    def audit_trail_for(self, resource_type: str, resource_id: str) -> list[AuditEntry]:
        return self._audit_log.list_for_resource(resource_type, resource_id)

    def grant_consent(self, user_id: str, consent_type: ConsentType) -> None:
        grant_consent(self._consent, user_id, consent_type)

    def revoke_consent(self, user_id: str, consent_type: ConsentType) -> None:
        revoke_consent(self._consent, user_id, consent_type)

    def has_active_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        return has_active_consent(self._consent, user_id, consent_type)

    def try_acquire_rate_limit(self, actor_id: str) -> bool:
        return self._rate_limiter.try_acquire(actor_id)

    def enqueue_failure(self, *, task_type: str, payload: dict, error: str) -> FailedTask:
        return enqueue_failure(self._failures, task_type=task_type, payload=payload, error=error)

    def pending_failures(self) -> list[FailedTask]:
        return self._failures.list_pending()

    def resolve_failure(self, task_id: str) -> FailedTask:
        return mark_resolved(self._failures, task_id)

    def retry_failure(self, task_id: str) -> FailedTask:
        return requeue_for_retry(self._failures, task_id)

    def register_data_exporter(self, source: str, exporter: DataExporter) -> None:
        self._portability.register_exporter(source, exporter)

    def register_data_deletor(self, source: str, deletor: DataDeletor) -> None:
        self._portability.register_deletor(source, deletor)

    def export_user_data(self, identity_id: str) -> dict[str, dict]:
        return self._portability.export_user_data(identity_id)

    def delete_user_data(self, identity_id: str) -> dict[str, bool]:
        return self._portability.delete_user_data(identity_id)
