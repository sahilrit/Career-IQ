"""Follow-up message generation for applications awaiting a response."""

from __future__ import annotations

from careeros_career_brain import Application


def generate_follow_up_message(application: Application, *, days_since_applied: int) -> str:
    day_word = "day" if days_since_applied == 1 else "days"
    return (
        f"Hi, I wanted to follow up on my application for the {application.job_title} "
        f"role at {application.company_name}, submitted {days_since_applied} {day_word} "
        "ago. I remain very interested and happy to answer any questions.\n\n"
        "Best regards\n"
    )
