"""Base exception hierarchy shared by every CareerOS package.

Package-specific errors (a future ``CareerBrainError``, ``PluginError``, ...)
should subclass ``CareerOSError`` rather than raising bare ``Exception`` or a
built-in exception type, so callers can catch any CareerOS failure as one
family regardless of which package raised it.
"""

from __future__ import annotations


class CareerOSError(Exception):
    """Base class for all errors raised by CareerOS code."""


class ConfigurationError(CareerOSError):
    """Raised when configuration is missing, malformed, or fails validation."""
