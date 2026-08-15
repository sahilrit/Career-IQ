"""careeros_human_in_the_loop: live browser execution with human
takeover — detect a problem, hand off, let a human resolve it, resume.
Never auto-solves captchas or bypasses obstacles.
"""

from careeros_human_in_the_loop.detectors import (
    Problem,
    ProblemDetector,
    SelectorAppearsDetector,
    SelectorMissingDetector,
    run_detectors,
)
from careeros_human_in_the_loop.handoff import HandoffRecord, HandoffSession, HandoffState
from careeros_human_in_the_loop.runner import ExecutionResult, resume, run_with_human_fallback

__all__ = [
    "ExecutionResult",
    "HandoffRecord",
    "HandoffSession",
    "HandoffState",
    "Problem",
    "ProblemDetector",
    "SelectorAppearsDetector",
    "SelectorMissingDetector",
    "resume",
    "run_detectors",
    "run_with_human_fallback",
]
