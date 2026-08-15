"""Platform info: what OS/Python/architecture CareerOS is actually
running on right now — real introspection via the standard library
``platform`` module, not a static claim.
"""

from __future__ import annotations

import platform
import sys

from pydantic import BaseModel


class PlatformInfo(BaseModel):
    os_name: str
    os_version: str
    architecture: str
    python_version: str
    is_supported_os: bool


_SUPPORTED_OS_NAMES = frozenset({"Darwin", "Linux", "Windows"})


def is_os_supported(os_name: str) -> bool:
    return os_name in _SUPPORTED_OS_NAMES


def collect_platform_info() -> PlatformInfo:
    os_name = platform.system()
    return PlatformInfo(
        os_name=os_name,
        os_version=platform.release(),
        architecture=platform.machine(),
        python_version=".".join(str(part) for part in sys.version_info[:3]),
        is_supported_os=is_os_supported(os_name),
    )
