"""Risk classification: which action types are inherently high-risk and
must always go to a human, regardless of autonomy mode.

This is CareerOS's hard boundary. FULL_AUTONOMOUS mode covers routine,
reversible actions (submitting a qualified application); it never covers
financial/legal commitments or identity-credential changes — those stay
gated no matter what mode is configured.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_autonomy.models import ActionRequest, RiskLevel

# Irreversible, financial/legal, or identity-sensitive actions. This set
# is intentionally NOT configurable via AutonomyStrategy — only a code
# change can touch it, so a permissive policy config can never weaken it.
HARD_HIGH_RISK_ACTION_TYPES: frozenset[str] = frozenset(
    {
        "accept_offer",
        "reject_offer",
        "sign_contract",
        "make_payment",
        "send_payment_details",
        "change_identity_credentials",
        "delete_account",
        "withdraw_application",
    }
)

RiskClassifier = Callable[[ActionRequest], RiskLevel]


def default_risk_classifier(request: ActionRequest) -> RiskLevel:
    if request.action_type in HARD_HIGH_RISK_ACTION_TYPES:
        return RiskLevel.HIGH

    if request.action_type == "submit_application":
        match_score = request.payload.get("match_score")
        if match_score is None or match_score < 0.6:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    return RiskLevel.MEDIUM  # unknown action types default to caution
