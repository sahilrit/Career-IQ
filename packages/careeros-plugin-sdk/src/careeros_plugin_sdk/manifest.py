"""Plugin manifest: static, declarative metadata every plugin provides.

The registry validates and reasons about a plugin entirely through its
manifest — it never imports or executes plugin code to learn what a
plugin declares it does.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


class PluginManifest(BaseModel):
    """Declarative plugin metadata.

    ``capabilities`` are the capability keys this plugin provides (e.g.
    ``"FIND_JOBS"`` — see Phase 6/24). ``dependencies`` maps another
    plugin's id to a version constraint (e.g. ``{"careeros-remoteok":
    "^1.0.0"}``) that must be satisfied before this plugin can be enabled.
    """

    id: str
    name: str
    version: str
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(default_factory=dict)
    settings_schema: dict[str, object] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _id_format(cls, value: str) -> str:
        if not _ID_RE.match(value):
            raise ValueError(
                f"Plugin id {value!r} must be lowercase and use only [a-z0-9_-], "
                "starting with a letter or digit"
            )
        return value

    @field_validator("version")
    @classmethod
    def _version_format(cls, value: str) -> str:
        if not _VERSION_RE.match(value):
            raise ValueError(f"Plugin version {value!r} must be MAJOR.MINOR.PATCH semver")
        return value
