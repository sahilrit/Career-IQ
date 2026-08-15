"""Core models for the autonomous decision & authorization system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AutonomyMode(StrEnum):
    MANUAL = "manual"
    SUPERVISED = "supervised"
    FULL_AUTONOMOUS = "full_autonomous"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ActionRequest:
    action_type: str
    subject_id: str
    payload: dict = field(default_factory=dict)
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AuthorizationDecision:
    approved: bool
    requires_human: bool
    risk_level: RiskLevel
    reason: str
