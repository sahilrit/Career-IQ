"""Tests for TemplateRecruiterOutreachGenerator."""

from __future__ import annotations

from careeros_career_brain import Recruiter
from careeros_employment_division import TemplateRecruiterOutreachGenerator


def test_message_mentions_recruiter_title_company_and_sender(brain, posting):
    recruiter = Recruiter(full_name="Jane Smith")
    message = TemplateRecruiterOutreachGenerator().generate(brain, recruiter, posting)

    assert "Jane Smith" in message
    assert "Backend Engineer" in message
    assert "Widget Co" in message
    assert message.strip().endswith("Ada Lovelace")


def test_message_mentions_matched_skills(brain, posting):
    recruiter = Recruiter(full_name="Jane Smith")
    message = TemplateRecruiterOutreachGenerator().generate(brain, recruiter, posting)
    assert "Python" in message


def test_message_falls_back_without_matched_skills(brain_factory, posting):
    brain = brain_factory(skills=[])
    recruiter = Recruiter(full_name="Jane Smith")
    message = TemplateRecruiterOutreachGenerator().generate(brain, recruiter, posting)
    assert "strong fit" in message
