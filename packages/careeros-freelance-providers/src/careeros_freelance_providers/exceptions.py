"""Freelance provider framework exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class FreelanceProviderError(CareerOSError):
    """Base class for all freelance provider errors (network, parsing, etc.)."""
