"""DecisionMaker: the real person at a predicted-demand company worth
starting a relationship with — always a name the user actually found,
never guessed.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "decision_maker"


class DecisionMaker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    name: str
    title: str = ""


class DecisionMakerRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, decision_maker: DecisionMaker) -> None:
        self._store.put(_ENTITY_TYPE, decision_maker.id, decision_maker.model_dump(mode="json"))

    def list_for_company(self, company_id: str) -> list[DecisionMaker]:
        return [
            DecisionMaker.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("company_id") == company_id
        ]
