"""Tests for the AnalyticsDivision facade."""

from __future__ import annotations

from datetime import date

from careeros_analytics import AnalyticsDivision
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity, Skill
from careeros_client_acquisition import Company, CompanyRepository
from careeros_crm import Contact, ContactRepository, ContactRole
from careeros_financial_intelligence import IncomeRecord, IncomeRepository, IncomeSource
from careeros_offer_negotiation import Offer, OfferRepository


def test_application_funnel_reads_across_all_brains(store):
    brain = CareerBrain(
        identity=Identity(full_name="Ada", email="ada@example.com"),
        applications=[Application(job_title="Engineer", company_name="Acme")],
    )
    CareerBrainRepository(store).save(brain)
    division = AnalyticsDivision(store)
    assert division.application_funnel().discovered_count == 1


def test_platform_performance_delegates(store):
    brain = CareerBrain(
        identity=Identity(full_name="Ada", email="ada@example.com"),
        applications=[
            Application(job_title="Engineer", company_name="Acme", source_provider="remoteok")
        ],
    )
    CareerBrainRepository(store).save(brain)
    division = AnalyticsDivision(store)
    assert "remoteok" in division.platform_performance()


def test_industry_performance_delegates(store):
    CompanyRepository(store).save(
        Company(name="A", website="https://a.example.com", industry="retail")
    )
    division = AnalyticsDivision(store)
    assert division.industry_performance() == {"retail": 1}


def test_freelance_funnel_delegates(store):
    CompanyRepository(store).save(Company(name="A", website="https://a.example.com"))
    division = AnalyticsDivision(store)
    assert division.freelance_funnel().lead_count == 1


def test_network_growth_delegates(store):
    ContactRepository(store).save(Contact(name="Jane", role=ContactRole.RECRUITER))
    division = AnalyticsDivision(store)
    assert division.network_growth().contact_count == 1


def test_career_roi_uses_the_first_brains_skills(store):
    brain = CareerBrain(
        identity=Identity(full_name="Ada", email="ada@example.com"),
        skills=[Skill(name="Python", proficiency=5)],
    )
    CareerBrainRepository(store).save(brain)
    IncomeRepository(store).save(
        IncomeRecord(
            source=IncomeSource.SALARY,
            source_name="Acme",
            amount=10_000,
            received_date=date(2026, 1, 1),
        )
    )
    OfferRepository(store).save(
        Offer(company_name="Acme", job_title="Engineer", base_salary=100_000)
    )
    ContactRepository(store).save(Contact(name="Jane", role=ContactRole.RECRUITER))

    division = AnalyticsDivision(store)
    roi = division.career_roi()

    assert roi.skill_count == 1
    assert roi.salary_income == 10_000
    assert roi.network_contact_count == 1
    assert roi.future_opportunity_value == 100_000


def test_career_roi_with_no_brain_has_zero_skill_count(store):
    division = AnalyticsDivision(store)
    assert division.career_roi().skill_count == 0
