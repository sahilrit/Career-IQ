"""OutcomeEvent: one real, observed result for a variant — sent,
response, interview, offer, client conversion, or revenue. Always
recorded from what actually happened elsewhere in the platform, never
simulated.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "outcome_event"


class OutcomeType(StrEnum):
    SENT = "sent"
    RESPONSE = "response"
    INTERVIEW = "interview"
    OFFER = "offer"
    CLIENT_CONVERSION = "client_conversion"
    REVENUE = "revenue"


class OutcomeEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    variant_id: str
    outcome_type: OutcomeType
    value: float = 1.0
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OutcomeEventRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, event: OutcomeEvent) -> None:
        self._store.put(_ENTITY_TYPE, event.id, event.model_dump(mode="json"))

    def list_for_variant(self, variant_id: str) -> list[OutcomeEvent]:
        return [
            OutcomeEvent.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("variant_id") == variant_id
        ]
