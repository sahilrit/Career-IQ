"""Tests for publish_version / current_version / rollback_to."""

from __future__ import annotations

import pytest

from careeros_marketplace_governance import (
    PluginVersionRepository,
    VersionNotFoundError,
    current_version,
    publish_version,
    rollback_to,
)


def test_publish_version_sets_it_current(store):
    repository = PluginVersionRepository(store)
    publish_version(repository, "careeros-example", "1.0.0")
    assert current_version(repository, "careeros-example") == "1.0.0"


def test_publishing_a_new_version_supersedes_the_old_one(store):
    repository = PluginVersionRepository(store)
    publish_version(repository, "careeros-example", "1.0.0")
    publish_version(repository, "careeros-example", "1.1.0")
    assert current_version(repository, "careeros-example") == "1.1.0"
    history = repository.list_for_plugin("careeros-example")
    assert [record.is_current for record in history] == [False, True]


def test_current_version_is_none_when_nothing_published(store):
    repository = PluginVersionRepository(store)
    assert current_version(repository, "careeros-example") is None


def test_rollback_to_restores_an_earlier_version(store):
    repository = PluginVersionRepository(store)
    publish_version(repository, "careeros-example", "1.0.0")
    publish_version(repository, "careeros-example", "1.1.0")
    rollback_to(repository, "careeros-example", "1.0.0")
    assert current_version(repository, "careeros-example") == "1.0.0"
    history = repository.list_for_plugin("careeros-example")
    current_flags = {record.version: record.is_current for record in history}
    assert current_flags == {"1.0.0": True, "1.1.0": False}


def test_rollback_to_an_unpublished_version_raises(store):
    repository = PluginVersionRepository(store)
    publish_version(repository, "careeros-example", "1.0.0")
    with pytest.raises(VersionNotFoundError):
        rollback_to(repository, "careeros-example", "9.9.9")


def test_version_history_is_isolated_per_plugin(store):
    repository = PluginVersionRepository(store)
    publish_version(repository, "careeros-a", "1.0.0")
    publish_version(repository, "careeros-b", "1.0.0")
    assert len(repository.list_for_plugin("careeros-a")) == 1
