"""Follow-up message generation for outreach awaiting a response."""

from __future__ import annotations

from careeros_client_acquisition.company import Company


def generate_follow_up_message(company: Company, *, days_since_outreach: int) -> str:
    day_word = "day" if days_since_outreach == 1 else "days"
    return (
        f"Hi{f' {company.contact_name}' if company.contact_name else ''}, I wanted to "
        f"follow up on my note to {company.name} from {days_since_outreach} {day_word} "
        "ago. Still happy to walk through what I found and how I'd fix it, whenever "
        "is convenient.\n\n"
        "Best regards\n"
    )
