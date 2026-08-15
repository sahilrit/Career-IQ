"""Client: a lightweight CRM entity for freelance relationship tracking.

Deliberately separate from careeros_career_brain's Company/Recruiter —
Phase 33 (CRM & Relationship Intelligence) builds full relationship
tracking across every kind of contact; this is the first, minimal
version scoped to what freelance opportunity intelligence needs right
now: who is this client, and where are we with them?
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "client"


class RelationshipStage(StrEnum):
    PROSPECT = "prospect"
    CONTACTED = "contacted"
    PROPOSAL_SENT = "proposal_sent"
    ACTIVE = "active"
    PAST = "past"


class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact_email: str | None = None
    stage: RelationshipStage = RelationshipStage.PROSPECT
    notes: str = ""


class ClientRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, client: Client) -> None:
        self._store.put(_ENTITY_TYPE, client.id, client.model_dump(mode="json"))

    def load(self, client_id: str) -> Client:
        return Client.model_validate(self._store.get(_ENTITY_TYPE, client_id))

    def load_or_none(self, client_id: str) -> Client | None:
        data = self._store.get_or_none(_ENTITY_TYPE, client_id)
        return Client.model_validate(data) if data is not None else None

    def find_by_name(self, name: str) -> Client | None:
        for data in self._store.list(_ENTITY_TYPE):
            if data.get("name") == name:
                return Client.model_validate(data)
        return None

    def list_all(self) -> list[Client]:
        return [Client.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
