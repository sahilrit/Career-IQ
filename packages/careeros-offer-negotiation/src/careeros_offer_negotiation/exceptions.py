"""Offer Evaluation & Negotiation Intelligence exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class OfferNegotiationError(CareerOSError):
    """Base class for all offer/negotiation errors."""
