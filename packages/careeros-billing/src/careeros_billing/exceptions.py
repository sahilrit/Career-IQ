"""SaaS Billing & Plans exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class BillingError(CareerOSError):
    """Base class for all billing errors."""


class SubscriptionNotFoundError(BillingError):
    """Raised when a workspace has no subscription record."""
