"""Tests for data_access.py."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from careeros_calendar_assistant import CalendarEvent, CalendarEventRepository
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity
from careeros_client_acquisition import Company, CompanyRepository
from careeros_crm import Contact, ContactRepository, ContactRole
from careeros_dashboard.data_access import (
    build_dashboard_summary,
    list_applications,
    list_pending_client_acquisition_tasks,
    list_upcoming_interviews,
    primary_brain,
)
from careeros_financial_intelligence import IncomeRecord, IncomeRepository, IncomeSource
from careeros_offer_negotiation import Offer, OfferRepository
from careeros_opportunity_intelligence import Client, ClientRepository, RelationshipStage

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def test_primary_brain_returns_none_when_store_is_empty(store):
    assert primary_brain(store) is None


def test_primary_brain_returns_the_first_saved_brain(store):
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    assert primary_brain(store).identity.email == "ada@example.com"


def test_list_applications_flattens_across_brains(store):
    brain = CareerBrain(
        identity=Identity(full_name="Ada", email="ada@example.com"),
        applications=[Application(job_title="Engineer", company_name="Acme")],
    )
    CareerBrainRepository(store).save(brain)
    assert len(list_applications(store)) == 1


def test_list_upcoming_interviews_excludes_past_events(store):
    past = CalendarEvent(title="Past interview", scheduled_at=_NOW - timedelta(days=1))
    future = CalendarEvent(title="Future interview", scheduled_at=_NOW + timedelta(days=1))
    CalendarEventRepository(store).save(past)
    CalendarEventRepository(store).save(future)
    upcoming = list_upcoming_interviews(store, now=_NOW)
    assert [event.title for event in upcoming] == ["Future interview"]


def test_list_upcoming_interviews_excludes_events_with_no_scheduled_time(store):
    CalendarEventRepository(store).save(CalendarEvent(title="Unscheduled"))
    assert list_upcoming_interviews(store, now=_NOW) == []


def test_list_pending_client_acquisition_tasks_reflects_next_stage(store):
    company = Company(name="Widget Co", website="https://widgetco.example.com")
    CompanyRepository(store).save(company)
    tasks = list_pending_client_acquisition_tasks(store)
    assert len(tasks) == 1
    assert "Widget Co" in tasks[0]
    assert "discovery" in tasks[0]


def test_build_dashboard_summary_aggregates_across_packages(store):
    brain = CareerBrain(
        identity=Identity(full_name="Ada", email="ada@example.com"),
        applications=[Application(job_title="Engineer", company_name="Acme")],
    )
    CareerBrainRepository(store).save(brain)
    CalendarEventRepository(store).save(
        CalendarEvent(title="Interview", scheduled_at=_NOW + timedelta(days=1))
    )
    OfferRepository(store).save(
        Offer(company_name="Acme", job_title="Engineer", base_salary=100_000)
    )
    CompanyRepository(store).save(Company(name="Widget Co", website="https://widgetco.example.com"))
    ClientRepository(store).save(Client(name="Acme Client", stage=RelationshipStage.ACTIVE))
    IncomeRepository(store).save(
        IncomeRecord(
            source=IncomeSource.FREELANCE,
            source_name="Acme Client",
            amount=500,
            received_date=date(2026, 1, 1),
        )
    )
    ContactRepository(store).save(Contact(name="Jane Smith", role=ContactRole.RECRUITER))

    summary = build_dashboard_summary(store, now=_NOW)

    assert summary.application_count == 1
    assert summary.upcoming_interview_count == 1
    assert summary.offer_count == 1
    assert summary.prospect_count == 1
    assert summary.active_client_count == 1
    assert summary.total_income == 500
    assert summary.network_contact_count == 1
    assert len(summary.pending_tasks) == 1


def test_build_dashboard_summary_with_empty_store_is_all_zero(store):
    summary = build_dashboard_summary(store, now=_NOW)
    assert summary.application_count == 0
    assert summary.total_income == 0
    assert summary.pending_tasks == []
