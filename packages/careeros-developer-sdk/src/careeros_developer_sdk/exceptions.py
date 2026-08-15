"""Developer SDK exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class DeveloperSdkError(CareerOSError):
    """Base class for all developer SDK errors."""


class UnknownActionError(DeveloperSdkError):
    """Raised when calling an action name the plugin never registered a handler for."""
