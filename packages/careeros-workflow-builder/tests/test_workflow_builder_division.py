"""Tests for the WorkflowBuilderDivision facade."""

from __future__ import annotations

import pytest

from careeros_event_bus import Event, EventBus
from careeros_workflow_builder import Rule, WorkflowBuilderDivision


@pytest.fixture
def division(rule_repository, executor):
    return WorkflowBuilderDivision(rule_repository, executor)


def test_add_rule_and_list_rules(division):
    rule = Rule(name="Rule", event_type="job.scored", actions=["a"])
    division.add_rule(rule)
    assert division.list_rules() == [rule]


def test_evaluate_runs_matching_rules(division, executor):
    calls = []
    executor.register("action", lambda event: calls.append(event))
    division.add_rule(Rule(name="Rule", event_type="job.scored", actions=["action"]))
    triggered = division.evaluate(Event(event_type="job.scored", payload={}))
    assert len(triggered) == 1
    assert len(calls) == 1


def test_wire_hooks_the_division_to_a_bus(division, executor):
    calls = []
    executor.register("action", lambda event: calls.append(event))
    division.add_rule(Rule(name="Rule", event_type="job.scored", actions=["action"]))
    bus = EventBus()
    division.wire(bus)
    bus.publish(Event(event_type="job.scored", payload={}))
    assert len(calls) == 1
