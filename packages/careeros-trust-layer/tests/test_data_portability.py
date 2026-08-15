"""Tests for the data export/deletion registry and the CareerBrain
reference exporter/deletor.
"""

from __future__ import annotations

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_trust_layer import (
    CareerBrainDataDeletor,
    CareerBrainDataExporter,
    DataPortabilityRegistry,
)


def test_career_brain_exporter_returns_none_when_missing(store):
    exporter = CareerBrainDataExporter(store)
    assert exporter.export("missing-id") is None


def test_career_brain_exporter_returns_the_brains_data(store):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    exporter = CareerBrainDataExporter(store)
    exported = exporter.export(brain.identity.id)
    assert exported["identity"]["full_name"] == "Ada Lovelace"


def test_career_brain_deletor_removes_the_brain(store):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    deletor = CareerBrainDataDeletor(store)
    assert deletor.delete(brain.identity.id) is True
    assert CareerBrainRepository(store).load_or_none(brain.identity.id) is None


def test_career_brain_deletor_returns_false_when_missing(store):
    deletor = CareerBrainDataDeletor(store)
    assert deletor.delete("missing-id") is False


def test_registry_exports_only_registered_sources_with_data(store):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    registry = DataPortabilityRegistry()
    registry.register_exporter("career_brain", CareerBrainDataExporter(store))
    exported = registry.export_user_data(brain.identity.id)
    assert set(exported) == {"career_brain"}


def test_registry_skips_sources_with_no_data(store):
    registry = DataPortabilityRegistry()
    registry.register_exporter("career_brain", CareerBrainDataExporter(store))
    assert registry.export_user_data("missing-id") == {}


def test_registry_deletes_across_every_registered_deletor(store):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    registry = DataPortabilityRegistry()
    registry.register_deletor("career_brain", CareerBrainDataDeletor(store))
    results = registry.delete_user_data(brain.identity.id)
    assert results == {"career_brain": True}
