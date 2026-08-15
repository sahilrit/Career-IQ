"""Tests for the ClientAcquisitionDivision facade."""

from __future__ import annotations

import pytest

from careeros_client_acquisition import (
    ClientAcquisitionDivision,
    ClientAcquisitionStage,
    IdealClientProfile,
    ManualCompanyDiscoveryProvider,
    ProblemSignal,
    SignalType,
    WebsiteSignalDetector,
)
from careeros_client_acquisition.discovery import CompanyDiscoveryQuery
from careeros_event_bus import EventBus
from careeros_opportunity_intelligence import RelationshipStage


@pytest.fixture
def division(company_repository, progress_repository, client_repository, company):
    bus = EventBus()
    provider = ManualCompanyDiscoveryProvider([company])
    return (
        ClientAcquisitionDivision(
            company_repository,
            progress_repository,
            client_repository,
            discovery_provider=provider,
            event_bus=bus,
        ),
        bus,
    )


def test_discover_saves_company_and_marks_discovery(division, company):
    div, bus = division
    results = div.discover(CompanyDiscoveryQuery())
    assert results == [company]
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.DISCOVERY
    assert bus.history("company.discovered")


def test_qualify_company_marks_qualification_when_it_qualifies(division, company):
    div, bus = division
    signal = ProblemSignal(signal_type=SignalType.NO_HTTPS, detail="d")
    is_qualified = div.qualify_company(company, [signal], IdealClientProfile(min_signal_count=1))
    assert is_qualified is True
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.QUALIFICATION
    assert bus.history("company.qualified")


def test_qualify_company_does_not_mark_stage_when_it_fails(division, company):
    div, bus = division
    is_qualified = div.qualify_company(company, [], IdealClientProfile(min_signal_count=1))
    assert is_qualified is False
    assert div.progress_for(company.id).current_stage is None
    assert not bus.history("company.qualified")


def test_detect_problems_marks_problem_detection(division, company, fake_session):
    div, _bus = division
    fake_session.set_query_all_results("meta[name='description']", [{"content": "desc"}])
    fake_session.set_visible(".testimonial")
    fake_session.set_visible("#chat-widget")
    fake_session.set_visible("body", text="x" * 250)
    signals = div.detect_problems(company, WebsiteSignalDetector(fake_session))
    assert signals == []
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.PROBLEM_DETECTION


def test_score_marks_opportunity_score(division, company):
    div, _bus = division
    signal = ProblemSignal(signal_type=SignalType.NO_HTTPS, detail="d")
    result = div.score(company, [signal])
    assert result == 20.0
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.OPPORTUNITY_SCORE


def test_generate_audit_marks_audit_and_publishes(division, company):
    div, bus = division
    report = div.generate_audit(company, [])
    assert report.company_id == company.id
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.AUDIT
    assert bus.history("company.audit_generated")


def test_draft_outreach_marks_outreach(division, company, brain):
    div, _bus = division
    report = div.generate_audit(company, [])
    message = div.draft_outreach(brain, company, report)
    assert company.name in message
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.OUTREACH


def test_draft_follow_up_marks_follow_up(division, company):
    div, _bus = division
    message = div.draft_follow_up(company, days_since_outreach=2)
    assert company.name in message
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.FOLLOW_UP


def test_mark_methods_advance_progress(division, company):
    div, _bus = division
    div.mark_proposal_sent(company)
    div.mark_call_scheduled(company)
    div.mark_contract_signed(company)
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.CONTRACT


def test_win_client_creates_active_client_and_marks_final_stage(division, company):
    div, bus = division
    client = div.win_client(company)
    assert client.name == company.name
    assert client.stage == RelationshipStage.ACTIVE
    assert div.progress_for(company.id).current_stage == ClientAcquisitionStage.CLIENT
    assert bus.history("client.won")
