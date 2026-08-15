"""Production application decisions: combine qualification score with
safeguards (rate limits, cooldowns) before treating an opportunity as
ready to actually apply to.

Phase 10's QualificationPolicy answers "is this worth pursuing?" in
isolation; this answers the more careful production question: "should we
actually submit an application right now, given everything else already
in flight?"
"""

from __future__ import annotations

from dataclasses import dataclass, field

from careeros_application_intelligence.safeguards import CompanyCooldown, DailyApplicationLimiter
from careeros_career_brain import Application, CareerBrain


@dataclass
class ApplicationDecision:
    should_apply: bool
    reasons: list[str] = field(default_factory=list)


def decide_to_apply(
    brain: CareerBrain,
    application: Application,
    *,
    daily_limiter: DailyApplicationLimiter,
    company_cooldown: CompanyCooldown,
    min_match_score: float = 0.6,
) -> ApplicationDecision:
    reasons: list[str] = []

    if application.match_score is None or application.match_score < min_match_score:
        reasons.append(
            f"match score {application.match_score} is below the {min_match_score} threshold"
        )

    if not daily_limiter.has_capacity(brain.identity.id):
        reasons.append("daily application limit reached")

    if company_cooldown.is_on_cooldown(brain, application.company_name):
        reasons.append(f"already applied to {application.company_name} within the cooldown window")

    return ApplicationDecision(should_apply=not reasons, reasons=reasons)
