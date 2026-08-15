"""careeros_workflow_builder: the Unified Automation & Workflow Builder.

No-code WHEN/THEN rules over platform events:

    WHEN job.score > 90
    THEN research_company -> build_resume -> create_cover_letter
      -> find_recruiter -> apply -> send_outreach -> update_crm

The engine only matches events and dispatches named actions in order —
it never knows what an action actually does; that's real capability
code elsewhere in the platform, wired in through an ActionExecutor.
"""

from careeros_workflow_builder.condition import ComparisonOperator, Condition, evaluate_condition
from careeros_workflow_builder.engine import ActionExecutor, CallableActionExecutor, WorkflowEngine
from careeros_workflow_builder.exceptions import UnknownActionError, WorkflowBuilderError
from careeros_workflow_builder.rule import Rule, RuleRepository
from careeros_workflow_builder.workflow_builder_division import WorkflowBuilderDivision

__all__ = [
    "ActionExecutor",
    "CallableActionExecutor",
    "ComparisonOperator",
    "Condition",
    "Rule",
    "RuleRepository",
    "UnknownActionError",
    "WorkflowBuilderDivision",
    "WorkflowBuilderError",
    "WorkflowEngine",
    "evaluate_condition",
]
