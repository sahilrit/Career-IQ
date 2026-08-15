"""careeros_autonomy: the autonomous decision & authorization system.

FULL_AUTONOMOUS mode means "no per-application approval for routine,
qualified opportunities" — it never means "no safety boundaries". HIGH
risk actions (financial/legal commitments, identity-credential changes)
always require a human, in every mode; that boundary lives in
``risk.HARD_HIGH_RISK_ACTION_TYPES`` and cannot be configured away by an
``AutonomyStrategy``.
"""

from careeros_autonomy.decision_memory import DecisionMemory, DecisionRecord
from careeros_autonomy.engine import AuthorizationEngine
from careeros_autonomy.models import ActionRequest, AuthorizationDecision, AutonomyMode, RiskLevel
from careeros_autonomy.pacing import PacingLimiter
from careeros_autonomy.policy import AutonomyPolicy
from careeros_autonomy.risk import (
    HARD_HIGH_RISK_ACTION_TYPES,
    RiskClassifier,
    default_risk_classifier,
)
from careeros_autonomy.strategy import AGGRESSIVE, BALANCED, CONSERVATIVE, AutonomyStrategy

__all__ = [
    "AGGRESSIVE",
    "BALANCED",
    "CONSERVATIVE",
    "HARD_HIGH_RISK_ACTION_TYPES",
    "ActionRequest",
    "AuthorizationDecision",
    "AuthorizationEngine",
    "AutonomyMode",
    "AutonomyPolicy",
    "AutonomyStrategy",
    "DecisionMemory",
    "DecisionRecord",
    "PacingLimiter",
    "RiskClassifier",
    "RiskLevel",
    "default_risk_classifier",
]
