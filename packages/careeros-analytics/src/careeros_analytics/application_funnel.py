"""Application funnel: response/interview/offer/acceptance rates
computed from each Application's real status history, not just its
current status — an application that was interviewed and then rejected
still counts as having reached "interview".
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_career_brain import Application, ApplicationStatus

_RESPONSE_STATUSES = frozenset(
    {
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.OFFER,
        ApplicationStatus.ACCEPTED,
    }
)


class ApplicationFunnelMetrics(BaseModel):
    discovered_count: int
    applied_count: int
    response_count: int
    interview_count: int
    offer_count: int
    accepted_count: int
    response_rate: float | None
    interview_rate: float | None
    offer_rate: float | None
    acceptance_rate: float | None


def _reached(application: Application, status: ApplicationStatus) -> bool:
    return application.status == status or any(
        change.status == status for change in application.history
    )


def _reached_any(application: Application, statuses: frozenset[ApplicationStatus]) -> bool:
    return application.status in statuses or any(
        change.status in statuses for change in application.history
    )


def compute_application_funnel(applications: list[Application]) -> ApplicationFunnelMetrics:
    discovered_count = len(applications)
    applied_count = sum(1 for a in applications if _reached(a, ApplicationStatus.APPLIED))
    response_count = sum(1 for a in applications if _reached_any(a, _RESPONSE_STATUSES))
    interview_count = sum(1 for a in applications if _reached(a, ApplicationStatus.INTERVIEWING))
    offer_count = sum(1 for a in applications if _reached(a, ApplicationStatus.OFFER))
    accepted_count = sum(1 for a in applications if _reached(a, ApplicationStatus.ACCEPTED))

    def rate(count: int) -> float | None:
        return count / applied_count if applied_count else None

    return ApplicationFunnelMetrics(
        discovered_count=discovered_count,
        applied_count=applied_count,
        response_count=response_count,
        interview_count=interview_count,
        offer_count=offer_count,
        accepted_count=accepted_count,
        response_rate=rate(response_count),
        interview_rate=rate(interview_count),
        offer_rate=rate(offer_count),
        acceptance_rate=rate(accepted_count),
    )
