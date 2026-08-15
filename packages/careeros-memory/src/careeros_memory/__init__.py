"""careeros_memory: working memory, history logs, analytics, and local
semantic search. Career Brain remains authoritative; everything here is
derived from it and from domain events.
"""

from careeros_memory.analytics import (
    applications_by_status,
    interview_rate,
    offer_rate,
    response_rate,
)
from careeros_memory.history import HistoryEntry, HistoryLog
from careeros_memory.semantic import LocalTfidfIndex, SemanticIndex
from careeros_memory.subscribers import attach_history_logging, record_event_in_history
from careeros_memory.working import WorkingMemory

__all__ = [
    "HistoryEntry",
    "HistoryLog",
    "LocalTfidfIndex",
    "SemanticIndex",
    "WorkingMemory",
    "applications_by_status",
    "attach_history_logging",
    "interview_rate",
    "offer_rate",
    "record_event_in_history",
    "response_rate",
]
