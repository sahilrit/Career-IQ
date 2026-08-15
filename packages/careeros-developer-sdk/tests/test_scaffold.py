"""Tests for generate_plugin_scaffold."""

from __future__ import annotations

import ast

from careeros_developer_sdk import generate_plugin_scaffold


def test_returns_the_expected_files():
    files = generate_plugin_scaffold("careeros-my-plugin", "careeros_my_plugin")
    assert set(files) == {
        "pyproject.toml",
        "src/careeros_my_plugin/__init__.py",
        "src/careeros_my_plugin/plugin.py",
        "tests/test_careeros_my_plugin.py",
    }


def test_pyproject_names_the_plugin():
    files = generate_plugin_scaffold("careeros-my-plugin", "careeros_my_plugin")
    assert 'name = "careeros-my-plugin"' in files["pyproject.toml"]


def test_generated_python_files_are_syntactically_valid():
    files = generate_plugin_scaffold("careeros-my-plugin", "careeros_my_plugin")
    for path, content in files.items():
        if path.endswith(".py"):
            ast.parse(content)


def test_plugin_module_references_the_plugin_id():
    files = generate_plugin_scaffold("careeros-my-plugin", "careeros_my_plugin")
    assert "careeros-my-plugin" in files["src/careeros_my_plugin/plugin.py"]


def test_generated_plugin_module_actually_builds_a_working_plugin():
    files = generate_plugin_scaffold("careeros-my-plugin", "careeros_my_plugin")
    namespace: dict[str, object] = {}
    exec(compile(files["src/careeros_my_plugin/plugin.py"], "plugin.py", "exec"), namespace)
    plugin = namespace["build_plugin"]()
    assert plugin.manifest.id == "careeros-my-plugin"
    assert "example_action" in plugin.manifest.actions
