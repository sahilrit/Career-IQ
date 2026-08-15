"""Persistence for Career Brain, backed by careeros_common's DocumentStore."""

from __future__ import annotations

from careeros_career_brain.brain import CareerBrain
from careeros_common import DocumentStore

_ENTITY_TYPE = "career_brain"


class CareerBrainRepository:
    """CRUD for ``CareerBrain`` aggregates, one document per identity id."""

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, brain: CareerBrain) -> None:
        self._store.put(_ENTITY_TYPE, brain.identity.id, brain.model_dump(mode="json"))

    def load(self, identity_id: str) -> CareerBrain:
        return CareerBrain.model_validate(self._store.get(_ENTITY_TYPE, identity_id))

    def load_or_none(self, identity_id: str) -> CareerBrain | None:
        data = self._store.get_or_none(_ENTITY_TYPE, identity_id)
        return CareerBrain.model_validate(data) if data is not None else None

    def list_all(self) -> list[CareerBrain]:
        return [CareerBrain.model_validate(d) for d in self._store.list(_ENTITY_TYPE)]

    def delete(self, identity_id: str) -> None:
        self._store.delete(_ENTITY_TYPE, identity_id)
