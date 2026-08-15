"""Simple aggregate analytics over Career Brain.

Deliberately plain arithmetic over structured, authoritative data — no ML
here. This is the seed for Phase 44's full analytics/Career ROI
reporting; it must stay correct and cheap to compute as that grows.
"""

from __future__ import annotations

from careeros_career_brain import Application, ApplicationStatus, CareerBrain


def _has_reached(application: Application, status: ApplicationStatus) -> bool:
    return any(change.status == status for change in application.history)


def applications_by_status(brain: CareerBrain) -> dict[str, int]:
    counts: dict[str, int] = {status.value: 0 for status in ApplicationStatus}
    for application in brain.applications:
        counts[application.status.value] += 1
    return counts


def _rate(brain: CareerBrain, *, reached: ApplicationStatus) -> float:
    """Share of applications that ever reached APPLIED which also reached ``reached``."""
    applied = [a for a in brain.applications if _has_reached(a, ApplicationStatus.APPLIED)]
    if not applied:
        return 0.0
    matching = [a for a in applied if _has_reached(a, reached)]
    return len(matching) / len(applied)


def response_rate(brain: CareerBrain) -> float:
    """Share of applied applications that ever moved past APPLIED into review."""
    return _rate(brain, reached=ApplicationStatus.IN_REVIEW)


def interview_rate(brain: CareerBrain) -> float:
    return _rate(brain, reached=ApplicationStatus.INTERVIEWING)


def offer_rate(brain: CareerBrain) -> float:
    return _rate(brain, reached=ApplicationStatus.OFFER)
