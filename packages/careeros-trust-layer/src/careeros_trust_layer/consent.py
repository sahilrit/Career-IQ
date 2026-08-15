"""Consent management: every grant or revocation is its own record, so
consent history is auditable — never overwritten in place. Whether
consent is currently active is a derived read, not a mutable flag.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "consent_record"


class ConsentType(StrEnum):
    DATA_PROCESSING = "data_processing"
    MARKETING_COMMUNICATIONS = "marketing_communications"
    THIRD_PARTY_SHARING = "third_party_sharing"
    AUTONOMOUS_ACTIONS = "autonomous_actions"
    NETWORK_INTELLIGENCE_SHARING = "network_intelligence_sharing"


class ConsentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    consent_type: ConsentType
    granted: bool
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConsentRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, record: ConsentRecord) -> None:
        self._store.put(_ENTITY_TYPE, record.id, record.model_dump(mode="json"))

    def list_for_user(self, user_id: str) -> list[ConsentRecord]:
        records = [
            ConsentRecord.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("user_id") == user_id
        ]
        records.sort(key=lambda record: record.recorded_at)
        return records


def grant_consent(
    repository: ConsentRepository, user_id: str, consent_type: ConsentType
) -> ConsentRecord:
    record = ConsentRecord(user_id=user_id, consent_type=consent_type, granted=True)
    repository.save(record)
    return record


def revoke_consent(
    repository: ConsentRepository, user_id: str, consent_type: ConsentType
) -> ConsentRecord:
    record = ConsentRecord(user_id=user_id, consent_type=consent_type, granted=False)
    repository.save(record)
    return record


def has_active_consent(
    repository: ConsentRepository, user_id: str, consent_type: ConsentType
) -> bool:
    matching = [
        record
        for record in repository.list_for_user(user_id)
        if record.consent_type == consent_type
    ]
    if not matching:
        return False
    return matching[-1].granted
