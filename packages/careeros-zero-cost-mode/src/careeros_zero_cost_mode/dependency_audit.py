"""Workspace dependency audit: flags any package whose declared
dependencies include a known-paid SDK. ``scan_dependencies`` is a pure
function over caller-supplied dependency lists (so it's testable
against fixtures without depending on the live repo's package list
ever staying the same); ``read_workspace_dependencies`` does the real
filesystem scan using ``tomllib`` (Python 3.12 standard library — no
new dependency needed) for an actual run against this repo.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

_KNOWN_PAID_PACKAGES = frozenset(
    {
        "openai",
        "anthropic",
        "cohere",
        "boto3",
        "twilio",
        "sendgrid",
        "stripe",
        "google-cloud-aiplatform",
    }
)


def scan_dependencies(
    dependencies_by_package: dict[str, list[str]],
    *,
    known_paid_packages: frozenset[str] = _KNOWN_PAID_PACKAGES,
) -> dict[str, list[str]]:
    """Maps package name to its flagged deps; clean packages are omitted."""
    flagged: dict[str, list[str]] = {}
    for package_name, dependencies in dependencies_by_package.items():
        hits = [
            dependency
            for dependency in dependencies
            if _base_name(dependency) in known_paid_packages
        ]
        if hits:
            flagged[package_name] = hits
    return flagged


def _base_name(dependency_spec: str) -> str:
    """Strips a version constraint like 'openai>=1.0' down to 'openai'."""
    for separator in ("==", ">=", "<=", "~=", ">", "<", "!=", "["):
        if separator in dependency_spec:
            dependency_spec = dependency_spec.split(separator, 1)[0]
    return dependency_spec.strip().lower()


def read_workspace_dependencies(packages_dir: str | Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for pyproject_path in sorted(Path(packages_dir).glob("*/pyproject.toml")):
        with pyproject_path.open("rb") as handle:
            data = tomllib.load(handle)
        project = data.get("project", {})
        result[project.get("name", pyproject_path.parent.name)] = list(
            project.get("dependencies", [])
        )
    return result
