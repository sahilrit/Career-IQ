"""Tests for WorkflowEngine / CallableActionExecutor."""

from __future__ import annotations

import pytest

from careeros_event_bus import Event, EventBus
from careeros_workflow_builder import (
    ComparisonOperator,
    Condition,
    Rule,
    UnknownActionError,
    WorkflowEngine,
)


@pytest.fixture
def engine(rule_repository, executor):
    return WorkflowEngine(rule_repository, executor)


def test_unconditional_rule_triggers_on_matching_event_type(rule_repository, engine, executor):
    calls = []
    executor.register("calendar_event", lambda event: calls.append(event.event_type))
    rule_repository.save(
        Rule(
            name="Interview confirmed",
            event_type="interview.confirmed",
            actions=["calendar_event"],
        )
    )
    triggered = engine.handle_event(Event(event_type="interview.confirmed", payload={}))
    assert len(triggered) == 1
    assert calls == ["interview.confirmed"]


def test_condition_gates_the_rule(rule_repository, engine, executor):
    calls = []
    executor.register("apply", lambda event: calls.append(event))
    rule_repository.save(
        Rule(
            name="High score",
            event_type="job.scored",
            condition=Condition(field="score", operator=ComparisonOperator.GT, value=90),
            actions=["apply"],
        )
    )
    engine.handle_event(Event(event_type="job.scored", payload={"score": 95}))
    assert len(calls) == 1
    engine.handle_event(Event(event_type="job.scored", payload={"score": 50}))
    assert len(calls) == 1


def test_actions_run_in_order(rule_repository, engine, executor):
    order = []
    executor.register("first", lambda event: order.append("first"))
    executor.register("second", lambda event: order.append("second"))
    rule_repository.save(Rule(name="Chain", event_type="job.scored", actions=["first", "second"]))
    engine.handle_event(Event(event_type="job.scored", payload={}))
    assert order == ["first", "second"]


def test_stops_the_chain_on_first_failure(rule_repository, engine, executor):
    order = []

    def failing(event):
        raise RuntimeError("boom")

    executor.register("first", lambda event: order.append("first"))
    executor.register("second", failing)
    executor.register("third", lambda event: order.append("third"))
    rule_repository.save(
        Rule(name="Chain", event_type="job.scored", actions=["first", "second", "third"])
    )
    engine.handle_event(Event(event_type="job.scored", payload={}))
    assert order == ["first"]


def test_disabled_rules_never_trigger(rule_repository, engine, executor):
    calls = []
    executor.register("action", lambda event: calls.append(event))
    rule_repository.save(
        Rule(name="Disabled", event_type="job.scored", actions=["action"], enabled=False)
    )
    engine.handle_event(Event(event_type="job.scored", payload={}))
    assert calls == []


def test_unrelated_event_type_does_not_trigger(rule_repository, engine, executor):
    calls = []
    executor.register("action", lambda event: calls.append(event))
    rule_repository.save(Rule(name="Rule", event_type="job.scored", actions=["action"]))
    engine.handle_event(Event(event_type="system.heartbeat", payload={}))
    assert calls == []


def test_wire_hooks_the_engine_to_a_bus(rule_repository, engine, executor):
    calls = []
    executor.register("action", lambda event: calls.append(event))
    rule_repository.save(Rule(name="Rule", event_type="job.scored", actions=["action"]))
    bus = EventBus()
    engine.wire(bus)
    bus.publish(Event(event_type="job.scored", payload={}))
    assert len(calls) == 1


def test_publishes_rule_triggered_event(rule_repository, executor):
    rule_repository.save(Rule(name="Rule", event_type="job.scored", actions=[]))
    bus = EventBus()
    engine = WorkflowEngine(rule_repository, executor, event_bus=bus)
    engine.handle_event(Event(event_type="job.scored", payload={}))
    assert bus.history("workflow.rule_triggered")


def test_publishes_action_failed_event(rule_repository, executor):
    def failing(event):
        raise RuntimeError("boom")

    executor.register("failing", failing)
    rule_repository.save(Rule(name="Rule", event_type="job.scored", actions=["failing"]))
    bus = EventBus()
    engine = WorkflowEngine(rule_repository, executor, event_bus=bus)
    engine.handle_event(Event(event_type="job.scored", payload={}))
    assert bus.history("workflow.action_failed")


def test_callable_action_executor_raises_for_unknown_action(executor):
    with pytest.raises(UnknownActionError):
        executor.execute("nonexistent", Event(event_type="job.scored", payload={}))
