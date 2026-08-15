"""Tests for `careeros brain` command logic."""

from __future__ import annotations

from careeros_cli.commands.brain import create_brain, format_brain_summary


def test_create_brain_persists_and_returns_it(context):
    brain = create_brain(context, full_name="Ada Lovelace", email="ada@example.com")
    assert context.repository.load(brain.identity.id).identity.full_name == "Ada Lovelace"


def test_format_brain_summary_includes_key_fields(context):
    brain = create_brain(
        context, full_name="Ada Lovelace", email="ada@example.com", headline="Engineer"
    )
    summary = format_brain_summary(brain)
    assert "Ada Lovelace <ada@example.com>" in summary
    assert "Engineer" in summary
    assert "Skills: 0" in summary


def test_format_brain_summary_lists_nonzero_application_statuses(context):
    from careeros_career_brain import Application

    brain = create_brain(context, full_name="Ada Lovelace", email="ada@example.com")
    brain.applications.append(Application(job_title="Engineer", company_name="Acme"))

    summary = format_brain_summary(brain)

    assert "discovered: 1" in summary
    assert "qualified" not in summary
