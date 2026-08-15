"""WorkflowEngine: matches incoming events against every enabled Rule
and dispatches the matched rule's action chain through a pluggable
``ActionExecutor``. This engine never knows what "research_company" or
"build_resume" actually do — that's real capability code elsewhere in
the platform, wired in by whoever constructs the executor. Actions run
in order and stop at the first failure, since later steps in a chain
like "research_company -> build_resume -> create_cover_letter" usually
depend on the ones before them.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from typing import Protocol

from careeros_event_bus import Event, EventBus
from careeros_workflow_builder.condition import evaluate_condition
from careeros_workflow_builder.exceptions import UnknownActionError
from careeros_workflow_builder.rule import Rule, RuleRepository


class ActionExecutor(Protocol):
    def execute(self, action_name: str, event: Event) -> None: ...


class CallableActionExecutor:
    """Maps action names to plain callables — the reference ActionExecutor."""

    def __init__(self, actions: dict[str, Callable[[Event], None]] | None = None) -> None:
        self._actions = dict(actions or {})

    def register(self, action_name: str, action: Callable[[Event], None]) -> None:
        self._actions[action_name] = action

    def execute(self, action_name: str, event: Event) -> None:
        if action_name not in self._actions:
            raise UnknownActionError(f"No action registered for {action_name!r}")
        self._actions[action_name](event)


class WorkflowEngine:
    def __init__(
        self,
        rule_repository: RuleRepository,
        executor: ActionExecutor,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self._rules = rule_repository
        self._executor = executor
        self._bus = event_bus

    def handle_event(self, event: Event) -> list[str]:
        """Runs every matching rule's actions; returns the triggered rule ids."""
        triggered: list[str] = []
        for rule in self._rules.list_enabled():
            if not fnmatch.fnmatchcase(event.event_type, rule.event_type):
                continue
            if rule.condition is not None and not evaluate_condition(rule.condition, event.payload):
                continue
            triggered.append(rule.id)
            self._run_actions(rule, event)
        return triggered

    def wire(self, bus: EventBus) -> None:
        bus.subscribe("*", self.handle_event)

    def _run_actions(self, rule: Rule, event: Event) -> None:
        for action_name in rule.actions:
            try:
                self._executor.execute(action_name, event)
            except Exception:
                self._publish("workflow.action_failed", {"rule_id": rule.id, "action": action_name})
                return
        self._publish("workflow.rule_triggered", {"rule_id": rule.id, "actions": rule.actions})

    def _publish(self, event_type: str, payload: dict) -> None:
        if self._bus is not None:
            self._bus.publish(Event(event_type=event_type, payload=payload))
