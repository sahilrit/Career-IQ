"""WorkflowBuilderDivision: the facade for managing rules and running
them against events, without the caller needing to construct a
WorkflowEngine directly.
"""

from __future__ import annotations

from careeros_event_bus import Event, EventBus
from careeros_workflow_builder.engine import ActionExecutor, WorkflowEngine
from careeros_workflow_builder.rule import Rule, RuleRepository


class WorkflowBuilderDivision:
    def __init__(self, rule_repository: RuleRepository, executor: ActionExecutor) -> None:
        self._rules = rule_repository
        self._engine = WorkflowEngine(rule_repository, executor)

    def add_rule(self, rule: Rule) -> None:
        self._rules.save(rule)

    def list_rules(self) -> list[Rule]:
        return self._rules.list_all()

    def wire(self, bus: EventBus) -> None:
        self._engine.wire(bus)

    def evaluate(self, event: Event) -> list[str]:
        return self._engine.handle_event(event)
