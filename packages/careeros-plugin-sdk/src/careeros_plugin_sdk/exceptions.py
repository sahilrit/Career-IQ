"""Plugin SDK exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class PluginError(CareerOSError):
    """Base class for all plugin SDK errors."""


class DuplicatePluginError(PluginError):
    """Raised when registering a plugin id that is already registered."""


class PluginNotFoundError(PluginError):
    """Raised when referencing a plugin id that is not registered."""


class PluginDependencyError(PluginError):
    """Raised when a plugin's declared dependencies are not satisfied."""


class PluginValidationError(PluginError):
    """Raised when a plugin manifest fails validation."""
