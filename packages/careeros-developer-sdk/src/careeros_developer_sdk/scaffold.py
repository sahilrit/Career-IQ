"""Plugin scaffold generation: the same structure
docs/development/setup.md documents for every workspace package
(pyproject.toml, src/<package>/__init__.py, tests/) — a pure function
returning file contents, so the caller decides whether and where to
actually write them.
"""

from __future__ import annotations


def generate_plugin_scaffold(plugin_id: str, package_name: str) -> dict[str, str]:
    pyproject = f"""[project]
name = "{plugin_id}"
version = "0.1.0"
description = ""
requires-python = ">=3.12"
dependencies = [
    "careeros-developer-sdk",
]

[tool.uv.sources]
careeros-developer-sdk = {{ workspace = true }}

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]
"""

    plugin_module = f'''"""{plugin_id}: a CareerOS plugin."""

from __future__ import annotations

from careeros_developer_sdk import PluginBuilder


def build_plugin():
    return (
        PluginBuilder("{plugin_id}", "{plugin_id}", "0.1.0")
        .description("TODO: describe what this plugin does")
        .action("example_action", lambda event: None)
        .build()
    )
'''

    init_module = f'''"""{package_name}: a CareerOS plugin package."""

from {package_name}.plugin import build_plugin

__all__ = ["build_plugin"]
'''

    test_module = f'''"""Tests for {package_name}."""

from __future__ import annotations

from {package_name} import build_plugin


def test_plugin_builds():
    plugin = build_plugin()
    assert plugin.manifest.id == "{plugin_id}"
'''

    return {
        "pyproject.toml": pyproject,
        f"src/{package_name}/__init__.py": init_module,
        f"src/{package_name}/plugin.py": plugin_module,
        f"tests/test_{package_name}.py": test_module,
    }
