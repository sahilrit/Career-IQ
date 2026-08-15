"""Tests for PluginRegistry: validation, dependency handling, lifecycle."""

from __future__ import annotations

import pytest

from careeros_plugin_sdk import (
    DuplicatePluginError,
    PluginDependencyError,
    PluginNotFoundError,
    PluginRegistry,
    PluginState,
)


@pytest.fixture
def registry():
    return PluginRegistry()


def test_register_then_get(registry, make_fake_plugin):
    plugin = make_fake_plugin("careeros-remoteok")
    registry.register(plugin)
    assert registry.get("careeros-remoteok") is plugin
    assert registry.state_of("careeros-remoteok") == PluginState.REGISTERED


def test_duplicate_registration_raises(registry, make_fake_plugin):
    registry.register(make_fake_plugin("careeros-remoteok"))
    with pytest.raises(DuplicatePluginError):
        registry.register(make_fake_plugin("careeros-remoteok"))


def test_get_missing_plugin_raises(registry):
    with pytest.raises(PluginNotFoundError):
        registry.get("does-not-exist")


def test_register_with_unmet_dependency_raises(registry, make_fake_plugin):
    plugin = make_fake_plugin("dependent", dependencies={"missing-dep": "^1.0.0"})
    with pytest.raises(PluginDependencyError):
        registry.register(plugin)


def test_register_with_unsatisfied_version_constraint_raises(registry, make_fake_plugin):
    registry.register(make_fake_plugin("base", version="1.0.0"))
    dependent = make_fake_plugin("dependent", dependencies={"base": "^2.0.0"})
    with pytest.raises(PluginDependencyError):
        registry.register(dependent)


def test_enable_calls_on_enable_hook_once(registry, make_fake_plugin):
    plugin = make_fake_plugin("careeros-remoteok")
    registry.register(plugin)
    registry.enable("careeros-remoteok")
    registry.enable("careeros-remoteok")
    assert plugin.enable_calls == 1
    assert registry.state_of("careeros-remoteok") == PluginState.ENABLED


def test_enable_requires_dependency_already_enabled(registry, make_fake_plugin):
    registry.register(make_fake_plugin("base", version="1.0.0"))
    dependent = make_fake_plugin("dependent", dependencies={"base": "^1.0.0"})
    registry.register(dependent)

    with pytest.raises(PluginDependencyError):
        registry.enable("dependent")

    registry.enable("base")
    registry.enable("dependent")
    assert registry.state_of("dependent") == PluginState.ENABLED


def test_disable_calls_hook_and_updates_state(registry, make_fake_plugin):
    plugin = make_fake_plugin("careeros-remoteok")
    registry.register(plugin)
    registry.enable("careeros-remoteok")
    registry.disable("careeros-remoteok")
    assert plugin.disable_calls == 1
    assert registry.state_of("careeros-remoteok") == PluginState.DISABLED


def test_disable_blocked_while_an_enabled_plugin_depends_on_it(registry, make_fake_plugin):
    registry.register(make_fake_plugin("base", version="1.0.0"))
    registry.register(make_fake_plugin("dependent", dependencies={"base": "^1.0.0"}))
    registry.enable("base")
    registry.enable("dependent")

    with pytest.raises(PluginDependencyError):
        registry.disable("base")


def test_unregister_blocked_while_still_a_dependency(registry, make_fake_plugin):
    registry.register(make_fake_plugin("base", version="1.0.0"))
    registry.register(make_fake_plugin("dependent", dependencies={"base": "^1.0.0"}))

    with pytest.raises(PluginDependencyError):
        registry.unregister("base")


def test_unregister_removes_plugin_independently_installable_and_removable(
    registry, make_fake_plugin
):
    plugin = make_fake_plugin("careeros-remoteok")
    registry.register(plugin)
    registry.enable("careeros-remoteok")
    registry.unregister("careeros-remoteok")

    assert plugin.disable_calls == 1
    with pytest.raises(PluginNotFoundError):
        registry.get("careeros-remoteok")


def test_find_by_capability_only_returns_enabled_plugins(registry, make_fake_plugin):
    finder = make_fake_plugin("careeros-remoteok", capabilities=["FIND_JOBS"])
    other = make_fake_plugin("careeros-other", capabilities=["FIND_JOBS"])
    registry.register(finder)
    registry.register(other)
    registry.enable("careeros-remoteok")

    assert registry.find_by_capability("FIND_JOBS") == [finder]


def test_list_all_returns_every_registered_plugin(registry, make_fake_plugin):
    a = make_fake_plugin("a")
    b = make_fake_plugin("b")
    registry.register(a)
    registry.register(b)
    assert set(registry.list_all()) == {a, b}
