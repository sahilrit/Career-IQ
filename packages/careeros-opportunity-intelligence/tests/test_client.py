"""Tests for Client / ClientRepository."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_opportunity_intelligence import Client, ClientRepository, RelationshipStage


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield ClientRepository(store)


def test_save_then_load_roundtrips(repository):
    client = Client(name="Acme Co", contact_email="hi@acme.example")
    repository.save(client)

    loaded = repository.load(client.id)
    assert loaded.name == "Acme Co"
    assert loaded.contact_email == "hi@acme.example"
    assert loaded.stage == RelationshipStage.PROSPECT


def test_load_or_none_returns_none_when_missing(repository):
    assert repository.load_or_none("does-not-exist") is None


def test_find_by_name(repository):
    repository.save(Client(name="Acme Co"))
    repository.save(Client(name="Widget Co"))

    found = repository.find_by_name("Widget Co")
    assert found is not None
    assert found.name == "Widget Co"
    assert repository.find_by_name("Nonexistent Co") is None


def test_list_all_returns_every_saved_client(repository):
    repository.save(Client(name="Acme Co"))
    repository.save(Client(name="Widget Co"))
    names = {client.name for client in repository.list_all()}
    assert names == {"Acme Co", "Widget Co"}


def test_stage_can_be_updated_and_resaved(repository):
    client = Client(name="Acme Co")
    repository.save(client)

    client.stage = RelationshipStage.PROPOSAL_SENT
    repository.save(client)

    assert repository.load(client.id).stage == RelationshipStage.PROPOSAL_SENT
