"""Version history and rollback: every publish is its own record (never
overwritten in place), so rolling back means re-marking an earlier
record current rather than trying to reconstruct lost history.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_common import DocumentStore
from careeros_marketplace_governance.exceptions import VersionNotFoundError

_ENTITY_TYPE = "plugin_version_record"


class PluginVersionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plugin_id: str
    version: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_current: bool = True


class PluginVersionRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, record: PluginVersionRecord) -> None:
        self._store.put(_ENTITY_TYPE, record.id, record.model_dump(mode="json"))

    def list_for_plugin(self, plugin_id: str) -> list[PluginVersionRecord]:
        records = [
            PluginVersionRecord.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("plugin_id") == plugin_id
        ]
        records.sort(key=lambda record: record.published_at)
        return records


def publish_version(
    repository: PluginVersionRepository, plugin_id: str, version: str
) -> PluginVersionRecord:
    for record in repository.list_for_plugin(plugin_id):
        if record.is_current:
            record.is_current = False
            repository.save(record)
    new_record = PluginVersionRecord(plugin_id=plugin_id, version=version, is_current=True)
    repository.save(new_record)
    return new_record


def current_version(repository: PluginVersionRepository, plugin_id: str) -> str | None:
    for record in repository.list_for_plugin(plugin_id):
        if record.is_current:
            return record.version
    return None


def rollback_to(
    repository: PluginVersionRepository, plugin_id: str, version: str
) -> PluginVersionRecord:
    records = repository.list_for_plugin(plugin_id)
    target = next((record for record in records if record.version == version), None)
    if target is None:
        raise VersionNotFoundError(f"{version!r} was never published for {plugin_id!r}")

    for record in records:
        if record.is_current and record.id != target.id:
            record.is_current = False
            repository.save(record)

    target.is_current = True
    repository.save(target)
    return target
