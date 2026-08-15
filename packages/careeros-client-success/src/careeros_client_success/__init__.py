"""careeros_client_success: the Client Success Division.

Manages the post-contract freelance client lifecycle: contracts,
deliverables, meetings, invoices, upsells, renewals, and referrals.

    One Client -> Repeat Client -> Long-term Client -> Referral
"""

from careeros_client_success.client_success_division import ClientSuccessDivision
from careeros_client_success.contract import Contract, ContractRepository, ContractStatus
from careeros_client_success.deliverable import (
    Deliverable,
    DeliverableRepository,
    DeliverableStatus,
)
from careeros_client_success.exceptions import ClientSuccessError
from careeros_client_success.invoice import (
    Invoice,
    InvoiceRepository,
    InvoiceStatus,
    outstanding_balance,
)
from careeros_client_success.lifecycle import ClientLifecycleStage, classify_client_lifecycle_stage
from careeros_client_success.meeting_note import MeetingNote, MeetingNoteRepository
from careeros_client_success.messaging import render_renewal_reminder, render_upsell_suggestion
from careeros_client_success.referral import ReferralRecord, ReferralRepository

__all__ = [
    "ClientLifecycleStage",
    "ClientSuccessDivision",
    "ClientSuccessError",
    "Contract",
    "ContractRepository",
    "ContractStatus",
    "Deliverable",
    "DeliverableRepository",
    "DeliverableStatus",
    "Invoice",
    "InvoiceRepository",
    "InvoiceStatus",
    "MeetingNote",
    "MeetingNoteRepository",
    "ReferralRecord",
    "ReferralRepository",
    "classify_client_lifecycle_stage",
    "outstanding_balance",
    "render_renewal_reminder",
    "render_upsell_suggestion",
]
