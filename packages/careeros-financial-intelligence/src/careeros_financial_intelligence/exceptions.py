"""Financial Intelligence exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class FinancialIntelligenceError(CareerOSError):
    """Base class for all financial intelligence errors."""
