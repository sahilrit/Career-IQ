"""Negotiation talking points and a call script, generated from the
real gap between an offer and the user's own stated target — and from
which real levers (bonus, PTO, equity) the offer leaves room on.
Deterministic and template-based; nothing about the company or its
constraints is invented.
"""

from __future__ import annotations

from careeros_offer_negotiation.offer import Offer

_LOW_PTO_DAYS = 15
_NO_BONUS = 0.0
_NO_EQUITY = 0.0


def generate_negotiation_talking_points(offer: Offer, target_base_salary: float) -> list[str]:
    points: list[str] = []
    gap = target_base_salary - offer.base_salary

    if gap > 0:
        points.append(
            f"Ask for an additional ${gap:,.0f} in base salary to reach your "
            f"${target_base_salary:,.0f} target."
        )
    else:
        points.append(
            "Base salary already meets or exceeds your target — "
            "focus negotiation on the other levers below."
        )

    if offer.bonus == _NO_BONUS:
        points.append("No signing bonus was offered — ask for one to bridge any remaining gap.")

    if offer.equity_value == _NO_EQUITY:
        points.append("No equity was offered — ask whether it's on the table.")

    if offer.pto_days < _LOW_PTO_DAYS:
        points.append(f"PTO is only {offer.pto_days} days — ask for more if salary won't move.")

    return points


def render_negotiation_script(offer: Offer, target_base_salary: float) -> str:
    points = generate_negotiation_talking_points(offer, target_base_salary)
    lines = [
        f"Thank you for the offer for {offer.job_title} at {offer.company_name} — "
        "I'm genuinely excited about this.",
        "",
        "Before I accept, I'd like to discuss a few things:",
        "",
    ]
    lines.extend(f"- {point}" for point in points)
    lines.append("")
    lines.append("I'm confident we can find something that works for both sides.")
    return "\n".join(lines) + "\n"
