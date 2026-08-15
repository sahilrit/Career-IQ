"""AI Audit & Proposal Engine exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class AuditProposalEngineError(CareerOSError):
    """Base class for all audit/proposal engine errors."""
