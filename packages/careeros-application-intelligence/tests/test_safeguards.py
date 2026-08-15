"""Tests for DailyApplicationLimiter and CompanyCooldown."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_application_intelligence import CompanyCooldown, DailyApplicationLimiter
from careeros_career_brain import Application, ApplicationStatus


def test_limiter_has_capacity_before_any_submissions(fake_clock):
    limiter = DailyApplicationLimiter(max_per_day=2, clock=fake_clock)
    assert limiter.has_capacity("user-1")


def test_limiter_runs_out_of_capacity_after_the_cap(fake_clock):
    limiter = DailyApplicationLimiter(max_per_day=2, clock=fake_clock)
    limiter.record_submission("user-1")
    limiter.record_submission("user-1")
    assert not limiter.has_capacity("user-1")


def test_limiter_capacity_is_per_identity(fake_clock):
    limiter = DailyApplicationLimiter(max_per_day=1, clock=fake_clock)
    limiter.record_submission("user-1")
    assert not limiter.has_capacity("user-1")
    assert limiter.has_capacity("user-2")


def test_limiter_capacity_restores_after_24_hours(fake_clock):
    limiter = DailyApplicationLimiter(max_per_day=1, clock=fake_clock)
    limiter.record_submission("user-1")
    assert not limiter.has_capacity("user-1")

    fake_clock.advance(86_400 + 1)

    assert limiter.has_capacity("user-1")


def _applied_application(company_name: str, applied_at: datetime) -> Application:
    app = Application(job_title="Engineer", company_name=company_name)
    app.transition_to(ApplicationStatus.QUALIFIED)
    app.transition_to(ApplicationStatus.APPLIED)
    app.history[-1].changed_at = applied_at
    return app


def test_no_cooldown_when_never_applied_to_that_company(brain_factory):
    brain = brain_factory()
    cooldown = CompanyCooldown(cooldown_days=90)
    assert not cooldown.is_on_cooldown(brain, "Acme")


def test_discovered_only_application_does_not_trigger_cooldown(brain_factory):
    app = Application(job_title="Engineer", company_name="Acme")
    brain = brain_factory(applications=[app])
    cooldown = CompanyCooldown(cooldown_days=90)
    assert not cooldown.is_on_cooldown(brain, "Acme")


def test_recent_application_triggers_cooldown(brain_factory):
    now = datetime(2026, 6, 1, tzinfo=UTC)
    app = _applied_application("Acme", applied_at=now - timedelta(days=10))
    brain = brain_factory(applications=[app])
    cooldown = CompanyCooldown(cooldown_days=90)
    assert cooldown.is_on_cooldown(brain, "Acme", as_of=now)


def test_cooldown_expires_after_the_window(brain_factory):
    now = datetime(2026, 6, 1, tzinfo=UTC)
    app = _applied_application("Acme", applied_at=now - timedelta(days=100))
    brain = brain_factory(applications=[app])
    cooldown = CompanyCooldown(cooldown_days=90)
    assert not cooldown.is_on_cooldown(brain, "Acme", as_of=now)
