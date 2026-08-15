"""AutonomyPolicy: the orchestrating entrypoint combining authorization,
pacing, and decision memory — publishing authorization.decided on the
event bus so any observer (a dashboard, an audit log) can react.
"""

from __future__ import annotations

from careeros_autonomy.decision_memory import DecisionMemory
from careeros_autonomy.engine import AuthorizationEngine
from careeros_autonomy.models import ActionRequest, AuthorizationDecision, AutonomyMode
from careeros_autonomy.pacing import PacingLimiter
from careeros_event_bus import Event, EventBus


class AutonomyPolicy:
    def __init__(
        self,
        *,
        mode: AutonomyMode,
        engine: AuthorizationEngine,
        pacing: PacingLimiter,
        decision_memory: DecisionMemory,
        event_bus: EventBus,
    ) -> None:
        self.mode = mode
        self.decision_memory = decision_memory
        self._engine = engine
        self._pacing = pacing
        self._bus = event_bus

    def evaluate(self, request: ActionRequest) -> AuthorizationDecision:
        decision = self._engine.authorize(request, self.mode)

        if decision.approved and not self._pacing.ready():
            decision = AuthorizationDecision(
                approved=False,
                requires_human=False,
                risk_level=decision.risk_level,
                reason=(
                    "Rate-limited: wait "
                    f"{self._pacing.seconds_until_ready():.1f}s before the next "
                    "autonomous action."
                ),
            )

        if decision.approved:
            self._pacing.record_action()

        self.decision_memory.record(request, decision, self.mode)
        self._bus.publish(
            Event(
                event_type="authorization.decided",
                source="autonomy-policy",
                payload={
                    "subject_id": request.subject_id,
                    "action_type": request.action_type,
                    "approved": decision.approved,
                    "requires_human": decision.requires_human,
                    "risk_level": decision.risk_level.value,
                    "reason": decision.reason,
                },
            )
        )
        return decision
