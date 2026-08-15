"""careeros_intelligence_network exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class IntelligenceNetworkError(CareerOSError):
    """Base class for all intelligence-network errors."""


class ConsentRequiredError(IntelligenceNetworkError):
    """Raised when contributing a signal without active network-sharing consent."""
