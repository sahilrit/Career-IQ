"""Saved searches + their 'already seen' set, so a digest can surface only the
NEW qualified matches since last time. Tenant-scoped."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

_ENTITY = "saved_search"


class _Store(Protocol):
    def put(self, entity_type: str, entity_id: str, data: dict) -> None: ...
    def get_or_none(self, entity_type: str, entity_id: str) -> dict | None: ...
    def list(self, entity_type: str) -> list[dict]: ...
    def delete(self, entity_type: str, entity_id: str) -> None: ...


class SavedSearch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    keywords: list[str]
    remote_only: bool = True
    seen_application_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SavedSearchRepository:
    def __init__(self, store: _Store) -> None:
        self._store = store

    def list_all(self) -> list[SavedSearch]:
        items = [SavedSearch(**raw) for raw in self._store.list(_ENTITY)]
        return sorted(items, key=lambda s: s.created_at)

    def get_or_none(self, search_id: str) -> SavedSearch | None:
        raw = self._store.get_or_none(_ENTITY, search_id)
        return SavedSearch(**raw) if raw else None

    def save(self, search: SavedSearch) -> None:
        self._store.put(_ENTITY, search.id, search.model_dump(mode="json"))

    def delete(self, search_id: str) -> None:
        self._store.delete(_ENTITY, search_id)
