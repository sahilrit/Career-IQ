"""careeros_application_intelligence: production application decisions
(score + rate limits + cooldowns) and outcome tracking on top of Career
Brain's own state machine.
"""

from careeros_application_intelligence.decision import ApplicationDecision, decide_to_apply
from careeros_application_intelligence.outcome import record_outcome
from careeros_application_intelligence.safeguards import CompanyCooldown, DailyApplicationLimiter

__all__ = [
    "ApplicationDecision",
    "CompanyCooldown",
    "DailyApplicationLimiter",
    "decide_to_apply",
    "record_outcome",
]
