"""Tests for Rule / RuleRepository."""

from __future__ import annotations

from careeros_workflow_builder import Rule


def test_save_and_load_round_trips(rule_repository):
    rule = Rule(name="High score apply", event_type="job.scored", actions=["research_company"])
    rule_repository.save(rule)
    assert rule_repository.load(rule.id) == rule


def test_list_enabled_excludes_disabled_rules(rule_repository):
    enabled = Rule(name="Enabled", event_type="job.scored", actions=["a"])
    disabled = Rule(name="Disabled", event_type="job.scored", actions=["a"], enabled=False)
    rule_repository.save(enabled)
    rule_repository.save(disabled)
    assert rule_repository.list_enabled() == [enabled]


def test_list_all_includes_every_rule(rule_repository):
    enabled = Rule(name="Enabled", event_type="job.scored", actions=["a"])
    disabled = Rule(name="Disabled", event_type="job.scored", actions=["a"], enabled=False)
    rule_repository.save(enabled)
    rule_repository.save(disabled)
    assert len(rule_repository.list_all()) == 2


def test_condition_defaults_to_none():
    rule = Rule(name="Unconditional", event_type="interview.confirmed", actions=["calendar_event"])
    assert rule.condition is None
