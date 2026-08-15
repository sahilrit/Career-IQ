"""Opportunity Prediction Engine exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class OpportunityPredictionError(CareerOSError):
    """Base class for all opportunity prediction errors."""
