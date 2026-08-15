"""Workflow Builder exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class WorkflowBuilderError(CareerOSError):
    """Base class for all workflow builder errors."""


class UnknownActionError(WorkflowBuilderError):
    """Raised when a rule references an action name no executor recognizes."""
