"""Renewal and upsell message generation — deterministic and
template-based, referencing only the contract's own real title and
delivered-work count, never inventing new services or results.
"""

from __future__ import annotations

from careeros_client_success.contract import Contract
from careeros_client_success.deliverable import Deliverable, DeliverableStatus


def render_renewal_reminder(contract: Contract) -> str:
    return (
        f"Hi — {contract.title} is coming up on its end date. "
        "Would you like to discuss renewing or extending the engagement?\n"
    )


def render_upsell_suggestion(contract: Contract, deliverables: list[Deliverable]) -> str:
    delivered = [d for d in deliverables if d.status == DeliverableStatus.APPROVED]
    if not delivered:
        return (
            f"Hi — as we wrap up {contract.title}, I'd love to hear whether there's "
            "more scope you'd like to tackle next.\n"
        )
    return (
        f"Hi — glad {len(delivered)} deliverable(s) on {contract.title} landed well. "
        "Happy to talk through what else might be worth tackling next.\n"
    )
