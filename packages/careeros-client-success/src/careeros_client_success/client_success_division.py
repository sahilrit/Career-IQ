"""ClientSuccessDivision: the facade tying contracts, deliverables,
meeting notes, invoices, referrals, and lifecycle classification
together for one client.
"""

from __future__ import annotations

from careeros_client_success.contract import Contract, ContractRepository
from careeros_client_success.deliverable import Deliverable, DeliverableRepository
from careeros_client_success.invoice import Invoice, InvoiceRepository, outstanding_balance
from careeros_client_success.lifecycle import ClientLifecycleStage, classify_client_lifecycle_stage
from careeros_client_success.meeting_note import MeetingNote, MeetingNoteRepository
from careeros_client_success.messaging import render_renewal_reminder, render_upsell_suggestion
from careeros_client_success.referral import ReferralRecord, ReferralRepository


class ClientSuccessDivision:
    def __init__(
        self,
        contract_repository: ContractRepository,
        deliverable_repository: DeliverableRepository,
        meeting_note_repository: MeetingNoteRepository,
        invoice_repository: InvoiceRepository,
        referral_repository: ReferralRepository,
    ) -> None:
        self._contracts = contract_repository
        self._deliverables = deliverable_repository
        self._meeting_notes = meeting_note_repository
        self._invoices = invoice_repository
        self._referrals = referral_repository

    def add_contract(self, contract: Contract) -> None:
        self._contracts.save(contract)

    def add_deliverable(self, deliverable: Deliverable) -> None:
        self._deliverables.save(deliverable)

    def add_meeting_note(self, note: MeetingNote) -> None:
        self._meeting_notes.save(note)

    def add_invoice(self, invoice: Invoice) -> None:
        self._invoices.save(invoice)

    def record_referral(self, referral: ReferralRecord) -> None:
        self._referrals.save(referral)

    def outstanding_balance_for_contract(self, contract_id: str) -> float:
        return outstanding_balance(self._invoices.list_for_contract(contract_id))

    def lifecycle_stage_for(self, client_id: str) -> ClientLifecycleStage | None:
        contracts = self._contracts.list_for_client(client_id)
        referral_count = len(self._referrals.list_for_client(client_id))
        return classify_client_lifecycle_stage(contracts, referral_count=referral_count)

    def renewal_reminder(self, contract_id: str) -> str:
        return render_renewal_reminder(self._contracts.load(contract_id))

    def upsell_suggestion(self, contract_id: str) -> str:
        contract = self._contracts.load(contract_id)
        deliverables = self._deliverables.list_for_contract(contract_id)
        return render_upsell_suggestion(contract, deliverables)
