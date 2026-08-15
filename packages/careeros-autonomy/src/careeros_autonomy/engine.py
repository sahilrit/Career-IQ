"""AuthorizationEngine: pure decision logic combining autonomy mode with
risk classification.

    MANUAL          -> every action requires a human
    SUPERVISED      -> LOW risk auto-approved, MEDIUM+ requires a human
    FULL_AUTONOMOUS -> LOW and MEDIUM risk auto-approved

HIGH risk always requires a human, in every mode — this is the hard
boundary the roadmap requires: no autonomy setting can authorize a
financial/legal commitment or an identity-credential change on its own.
"""

from __future__ import annotations

from careeros_autonomy.models import ActionRequest, AuthorizationDecision, AutonomyMode, RiskLevel
from careeros_autonomy.risk import RiskClassifier, default_risk_classifier


class AuthorizationEngine:
    def __init__(self, risk_classifier: RiskClassifier = default_risk_classifier) -> None:
        self._risk_classifier = risk_classifier

    def authorize(self, request: ActionRequest, mode: AutonomyMode) -> AuthorizationDecision:
        risk_level = self._risk_classifier(request)

        if risk_level == RiskLevel.HIGH:
            return AuthorizationDecision(
                approved=False,
                requires_human=True,
                risk_level=risk_level,
                reason=(
                    f"{request.action_type!r} is always high-risk and requires human "
                    "approval, regardless of autonomy mode."
                ),
            )

        if mode == AutonomyMode.MANUAL:
            return AuthorizationDecision(
                approved=False,
                requires_human=True,
                risk_level=risk_level,
                reason="Autonomy mode is MANUAL: every action requires human approval.",
            )

        if mode == AutonomyMode.SUPERVISED:
            if risk_level == RiskLevel.LOW:
                return AuthorizationDecision(
                    approved=True,
                    requires_human=False,
                    risk_level=risk_level,
                    reason="Low-risk action auto-approved under SUPERVISED mode.",
                )
            return AuthorizationDecision(
                approved=False,
                requires_human=True,
                risk_level=risk_level,
                reason="Medium-risk action requires human approval under SUPERVISED mode.",
            )

        return AuthorizationDecision(
            approved=True,
            requires_human=False,
            risk_level=risk_level,
            reason=f"{risk_level.value}-risk action auto-approved under FULL_AUTONOMOUS mode.",
        )
