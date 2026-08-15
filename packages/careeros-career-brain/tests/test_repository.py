"""Tests for CareerBrainRepository."""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity, Skill
from careeros_common import DocumentStore


@pytest.fixture
def repo():
    with DocumentStore() as store:
        yield CareerBrainRepository(store)


def test_save_then_load_roundtrips(repo):
    brain = CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        skills=[Skill(name="Mathematics")],
    )
    repo.save(brain)

    loaded = repo.load(brain.identity.id)
    assert loaded.identity.full_name == "Ada Lovelace"
    assert loaded.skills[0].name == "Mathematics"


def test_load_or_none_returns_none_when_missing(repo):
    assert repo.load_or_none("does-not-exist") is None


def test_save_overwrites_previous_version(repo):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    repo.save(brain)

    brain.skills.append(Skill(name="Python"))
    repo.save(brain)

    loaded = repo.load(brain.identity.id)
    assert len(loaded.skills) == 1


def test_list_all_returns_every_saved_brain(repo):
    a = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    b = CareerBrain(identity=Identity(full_name="Grace Hopper", email="grace@example.com"))
    repo.save(a)
    repo.save(b)

    names = {brain.identity.full_name for brain in repo.list_all()}
    assert names == {"Ada Lovelace", "Grace Hopper"}


def test_delete_removes_the_brain(repo):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    repo.save(brain)
    repo.delete(brain.identity.id)
    assert repo.load_or_none(brain.identity.id) is None
