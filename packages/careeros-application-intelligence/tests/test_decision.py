"""Tests for decide_to_apply combining score + safeguards."""

from __future__ import annotations

from careeros_application_intelligence import (
    CompanyCooldown,
    DailyApplicationLimiter,
    decide_to_apply,
)
from careeros_career_brain import Application


def _decision(brain_factory, fake_clock, *, match_score=0.9, max_per_day=10, cooldown_days=0):
    application = Application(job_title="Engineer", company_name="Acme", match_score=match_score)
    brain = brain_factory(applications=[application])
    limiter = DailyApplicationLimiter(max_per_day=max_per_day, clock=fake_clock)
    cooldown = CompanyCooldown(cooldown_days=cooldown_days)
    return decide_to_apply(brain, application, daily_limiter=limiter, company_cooldown=cooldown)


def test_approves_when_everything_checks_out(brain_factory, fake_clock):
    decision = _decision(brain_factory, fake_clock)
    assert decision.should_apply is True
    assert decision.reasons == []


def test_rejects_low_match_score(brain_factory, fake_clock):
    decision = _decision(brain_factory, fake_clock, match_score=0.1)
    assert decision.should_apply is False
    assert any("match score" in reason for reason in decision.reasons)


def test_rejects_when_score_is_missing(brain_factory, fake_clock):
    decision = _decision(brain_factory, fake_clock, match_score=None)
    assert decision.should_apply is False


def test_rejects_when_daily_limit_exhausted(brain_factory, fake_clock):
    application = Application(job_title="Engineer", company_name="Acme", match_score=0.9)
    brain = brain_factory(applications=[application])
    limiter = DailyApplicationLimiter(max_per_day=1, clock=fake_clock)
    limiter.record_submission(brain.identity.id)
    cooldown = CompanyCooldown(cooldown_days=0)

    decision = decide_to_apply(brain, application, daily_limiter=limiter, company_cooldown=cooldown)

    assert decision.should_apply is False
    assert any("daily application limit" in reason for reason in decision.reasons)


def test_can_report_multiple_reasons_at_once(brain_factory, fake_clock):
    decision = _decision(brain_factory, fake_clock, match_score=0.1, max_per_day=0)
    assert decision.should_apply is False
    assert len(decision.reasons) == 2
