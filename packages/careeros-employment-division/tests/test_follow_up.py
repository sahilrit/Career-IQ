"""Tests for generate_follow_up_message."""

from __future__ import annotations

from careeros_career_brain import Application
from careeros_employment_division import generate_follow_up_message


def test_message_mentions_job_title_and_company():
    application = Application(job_title="Backend Engineer", company_name="Widget Co")
    message = generate_follow_up_message(application, days_since_applied=5)
    assert "Backend Engineer" in message
    assert "Widget Co" in message
    assert "5 days" in message


def test_singular_day_is_grammatically_correct():
    application = Application(job_title="Engineer", company_name="Acme")
    message = generate_follow_up_message(application, days_since_applied=1)
    assert "1 day " in message
    assert "1 days" not in message
