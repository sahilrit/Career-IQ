"""Tests for PluginBuilder."""

from __future__ import annotations

import pytest

from careeros_developer_sdk import PluginBuilder, UnknownActionError


def test_minimal_build_produces_a_valid_manifest():
    plugin = PluginBuilder("my-plugin", "My Plugin", "1.0.0").build()
    assert plugin.manifest.id == "my-plugin"
    assert plugin.manifest.name == "My Plugin"
    assert plugin.manifest.version == "1.0.0"


def test_description_capability_and_permission_are_recorded():
    plugin = (
        PluginBuilder("my-plugin", "My Plugin", "1.0.0")
        .description("Does things.")
        .capability("FIND_JOBS")
        .permission("network")
        .build()
    )
    assert plugin.manifest.description == "Does things."
    assert plugin.manifest.capabilities == ["FIND_JOBS"]
    assert plugin.manifest.permissions == ["network"]


def test_actions_are_derived_from_registered_handlers():
    plugin = (
        PluginBuilder("my-plugin", "My Plugin", "1.0.0")
        .action("discover_jobs", lambda: "found jobs")
        .action("apply", lambda: "applied")
        .build()
    )
    assert set(plugin.manifest.actions) == {"discover_jobs", "apply"}


def test_call_action_invokes_the_registered_handler():
    plugin = (
        PluginBuilder("my-plugin", "My Plugin", "1.0.0")
        .action("greet", lambda name: f"hello {name}")
        .build()
    )
    assert plugin.call_action("greet", "world") == "hello world"


def test_call_action_raises_for_an_unregistered_action():
    plugin = PluginBuilder("my-plugin", "My Plugin", "1.0.0").build()
    with pytest.raises(UnknownActionError):
        plugin.call_action("nonexistent")


def test_trigger_tool_workflow_and_health_check_are_recorded():
    plugin = (
        PluginBuilder("my-plugin", "My Plugin", "1.0.0")
        .trigger("job.scored")
        .tool("search_jobs")
        .workflow("default_apply")
        .action("discover_jobs", lambda: None)
        .health_check("discover_jobs")
        .build()
    )
    assert plugin.manifest.triggers == ["job.scored"]
    assert plugin.manifest.tools == ["search_jobs"]
    assert plugin.manifest.workflows == ["default_apply"]
    assert plugin.manifest.health_check_action == "discover_jobs"


def test_dependency_and_setting_are_recorded():
    plugin = (
        PluginBuilder("my-plugin", "My Plugin", "1.0.0")
        .dependency("careeros-core-plugin", "^1.0.0")
        .setting("api_key", {"type": "string"})
        .build()
    )
    assert plugin.manifest.dependencies == {"careeros-core-plugin": "^1.0.0"}
    assert plugin.manifest.settings_schema == {"api_key": {"type": "string"}}


def test_on_enable_and_on_disable_callbacks_fire():
    calls = []
    plugin = (
        PluginBuilder("my-plugin", "My Plugin", "1.0.0")
        .on_enable(lambda: calls.append("enabled"))
        .on_disable(lambda: calls.append("disabled"))
        .build()
    )
    plugin.on_enable()
    plugin.on_disable()
    assert calls == ["enabled", "disabled"]


def test_build_returns_a_fresh_plugin_each_time():
    builder = PluginBuilder("my-plugin", "My Plugin", "1.0.0")
    first = builder.build()
    second = builder.build()
    assert first is not second
    assert first.manifest.id == second.manifest.id
