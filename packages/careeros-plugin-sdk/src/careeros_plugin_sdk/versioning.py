"""Minimal semantic version parsing and constraint matching.

Just enough for plugin dependency constraints ("^1.2.3", ">=1.0.0", exact
"1.2.3") without pulling in an external semver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_plugin_sdk.exceptions import PluginValidationError


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str) -> Version:
        parts = raw.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise PluginValidationError(f"{raw!r} is not a MAJOR.MINOR.PATCH version")
        major, minor, patch = (int(p) for p in parts)
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def satisfies(version: str, constraint: str) -> bool:
    """Check whether ``version`` satisfies ``constraint``.

    Supported forms: exact (``"1.2.3"``), caret (``"^1.2.3"`` — same
    major and >= the given version, or for a ``0.x`` base, same
    major.minor), and ``">=1.2.3"``.
    """
    v = Version.parse(version)
    constraint = constraint.strip()

    if constraint.startswith("^"):
        base = Version.parse(constraint[1:])
        if base.major > 0:
            return v.major == base.major and v >= base
        return v.major == 0 and v.minor == base.minor and v >= base

    if constraint.startswith(">="):
        base = Version.parse(constraint[2:].strip())
        return v >= base

    return v == Version.parse(constraint)
