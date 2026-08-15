"""Read-side data access for the dashboard: pure functions over the
same DocumentStore every other package writes to, with no Streamlit
import in this module — the UI layer renders what these return, it
doesn't decide what counts as "upcoming" or "active" itself.

Single-tenant for now: ``primary_brain`` takes the first Career Brain
found. Real per-request tenant resolution (Phase 25's tenancy) is
future work for this UI layer, same as the CLI's current scope.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from careeros_calendar_assistant import CalendarEvent, CalendarEventRepository
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository
from careeros_client_acquisition import ClientAcquisitionProgressRepository, CompanyRepository
from careeros_common import DocumentStore
from careeros_crm import ContactRepository
from careeros_financial_intelligence import IncomeRepository
from careeros_offer_negotiation import OfferRepository
from careeros_opportunity_intelligence import ClientRepository, RelationshipStage

DEFAULT_DATA_DIR = Path(".careeros/data")


def open_store(data_dir: Path | str = DEFAULT_DATA_DIR) -> DocumentStore:
    return DocumentStore(Path(data_dir) / "careeros.db")


class DashboardSummary(BaseModel):
    application_count: int
    upcoming_interview_count: int
    offer_count: int
    prospect_count: int
    active_client_count: int
    total_income: float
    network_contact_count: int
    pending_tasks: list[str]


def primary_brain(store: DocumentStore) -> CareerBrain | None:
    brains = CareerBrainRepository(store).list_all()
    return brains[0] if brains else None


def list_applications(store: DocumentStore) -> list[Application]:
    return [
        application
        for brain in CareerBrainRepository(store).list_all()
        for application in brain.applications
    ]


def list_upcoming_interviews(
    store: DocumentStore, *, now: datetime | None = None
) -> list[CalendarEvent]:
    current_time = now or datetime.now(UTC)
    events = CalendarEventRepository(store).list_all()
    return [
        event
        for event in events
        if event.scheduled_at is not None and event.scheduled_at >= current_time
    ]


def list_pending_client_acquisition_tasks(store: DocumentStore) -> list[str]:
    companies = CompanyRepository(store).list_all()
    progress_repository = ClientAcquisitionProgressRepository(store)
    tasks = []
    for company in companies:
        progress = progress_repository.load(company.id)
        if progress.next_stage is not None:
            tasks.append(f"{company.name}: next step is {progress.next_stage.value}")
    return tasks


def build_dashboard_summary(
    store: DocumentStore, *, now: datetime | None = None
) -> DashboardSummary:
    applications = list_applications(store)
    upcoming_interviews = list_upcoming_interviews(store, now=now)
    offers = OfferRepository(store).list_all()
    companies = CompanyRepository(store).list_all()
    clients = ClientRepository(store).list_all()
    active_clients = [client for client in clients if client.stage == RelationshipStage.ACTIVE]
    income_records = IncomeRepository(store).list_all()
    contacts = ContactRepository(store).list_all()

    return DashboardSummary(
        application_count=len(applications),
        upcoming_interview_count=len(upcoming_interviews),
        offer_count=len(offers),
        prospect_count=len(companies),
        active_client_count=len(active_clients),
        total_income=sum(record.amount for record in income_records),
        network_contact_count=len(contacts),
        pending_tasks=list_pending_client_acquisition_tasks(store),
    )
