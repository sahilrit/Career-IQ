"""ExecutionContext: the shared context threaded through every capability
invocation — which identity (and, from Phase 25, which tenant) this
action is for, plus a correlation id for tracing one logical operation
across multiple packages/events.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionContext:
    identity_id: str
    tenant_id: str | None = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def child(self) -> ExecutionContext:
        """A new context for a sub-operation: same identity/tenant, fresh correlation id."""
        return ExecutionContext(identity_id=self.identity_id, tenant_id=self.tenant_id)
