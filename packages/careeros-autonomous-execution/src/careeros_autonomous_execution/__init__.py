"""careeros_autonomous_execution: the capstone integration connecting
Career Brain, opportunity scoring, the Application Engine, the Autonomy
System, and the real browser Application Runner into one continuous
autonomous loop, with human-in-the-loop fallback at every failure point.
"""

from careeros_autonomous_execution.executor import (
    AutonomousApplicationExecutor,
    ExecutionOutcome,
    ExecutionRun,
    FormMappingResolver,
    PostingResolver,
)

__all__ = [
    "AutonomousApplicationExecutor",
    "ExecutionOutcome",
    "ExecutionRun",
    "FormMappingResolver",
    "PostingResolver",
]
