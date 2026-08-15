"""ReferralRecord: a client referring a new prospect — always something
the user learned actually happened, never inferred.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "referral"


class ReferralRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    referred_name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReferralRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, referral: ReferralRecord) -> None:
        self._store.put(_ENTITY_TYPE, referral.id, referral.model_dump(mode="json"))

    def list_for_client(self, client_id: str) -> list[ReferralRecord]:
        return [
            ReferralRecord.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("client_id") == client_id
        ]
