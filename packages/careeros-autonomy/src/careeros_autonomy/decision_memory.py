"""DecisionMemory: an auditable record of every authorization decision.

Every autonomous action should be explainable — WHO (subject_id), WHAT
(action_type), WHY (reason), WHEN (decided_at), WHICH POLICY (mode,
risk_level). This is the first version of that record; Phase 45
(Security & Trust Layer) builds full audit logging on top of it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_autonomy.models import ActionRequest, AuthorizationDecision, AutonomyMode, RiskLevel
from careeros_common import DocumentStore

_ENTITY_TYPE = "authorization_decision"


class DecisionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str
    subject_id: str
    mode: AutonomyMode
    risk_level: RiskLevel
    approved: bool
    requires_human: bool
    reason: str
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DecisionMemory:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def record(
        self, request: ActionRequest, decision: AuthorizationDecision, mode: AutonomyMode
    ) -> DecisionRecord:
        record = DecisionRecord(
            action_type=request.action_type,
            subject_id=request.subject_id,
            mode=mode,
            risk_level=decision.risk_level,
            approved=decision.approved,
            requires_human=decision.requires_human,
            reason=decision.reason,
        )
        self._store.put(_ENTITY_TYPE, record.id, record.model_dump(mode="json"))
        return record

    def all(self) -> list[DecisionRecord]:
        return [DecisionRecord.model_validate(d) for d in self._store.list(_ENTITY_TYPE)]

    def for_action_type(self, action_type: str) -> list[DecisionRecord]:
        return [record for record in self.all() if record.action_type == action_type]

    def approval_rate(self, action_type: str | None = None) -> float:
        records = self.for_action_type(action_type) if action_type else self.all()
        if not records:
            return 0.0
        approved = sum(1 for record in records if record.approved)
        return approved / len(records)
