"""Data export and deletion: an extensible registry rather than one
function that has to know about every package's storage — each package
that owns identity-linked data registers its own exporter/deletor, the
same plugin-registry philosophy as Phase 3/24. CareerBrain (Phase 2,
the platform's one authoritative identity store) ships as the
reference implementation; other packages can register their own as
they're built.
"""

from __future__ import annotations

from typing import Protocol

from careeros_career_brain import CareerBrainRepository
from careeros_common import DocumentStore


class DataExporter(Protocol):
    def export(self, identity_id: str) -> dict | None: ...


class DataDeletor(Protocol):
    def delete(self, identity_id: str) -> bool: ...


class CareerBrainDataExporter:
    def __init__(self, store: DocumentStore) -> None:
        self._repository = CareerBrainRepository(store)

    def export(self, identity_id: str) -> dict | None:
        brain = self._repository.load_or_none(identity_id)
        return brain.model_dump(mode="json") if brain is not None else None


class CareerBrainDataDeletor:
    def __init__(self, store: DocumentStore) -> None:
        self._repository = CareerBrainRepository(store)

    def delete(self, identity_id: str) -> bool:
        if self._repository.load_or_none(identity_id) is None:
            return False
        self._repository.delete(identity_id)
        return True


class DataPortabilityRegistry:
    def __init__(self) -> None:
        self._exporters: dict[str, DataExporter] = {}
        self._deletors: dict[str, DataDeletor] = {}

    def register_exporter(self, source: str, exporter: DataExporter) -> None:
        self._exporters[source] = exporter

    def register_deletor(self, source: str, deletor: DataDeletor) -> None:
        self._deletors[source] = deletor

    def export_user_data(self, identity_id: str) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for source, exporter in self._exporters.items():
            data = exporter.export(identity_id)
            if data is not None:
                result[source] = data
        return result

    def delete_user_data(self, identity_id: str) -> dict[str, bool]:
        return {source: deletor.delete(identity_id) for source, deletor in self._deletors.items()}
