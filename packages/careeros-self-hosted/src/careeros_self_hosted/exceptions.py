"""Local / Self-Hosted Edition exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class SelfHostedError(CareerOSError):
    """Base class for all self-hosted edition errors."""
