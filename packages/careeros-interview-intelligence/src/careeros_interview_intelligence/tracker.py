"""BriefingTracker: remembers which milestones have already fired for
each calendar event, so a periodic check doesn't regenerate the same
briefing repeatedly.
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_interview_intelligence.schedule import BriefingMilestone

_ENTITY_TYPE = "briefing_tracker"


class BriefingTracker:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def fired_milestones(self, calendar_event_id: str) -> set[BriefingMilestone]:
        data = self._store.get_or_none(_ENTITY_TYPE, calendar_event_id)
        if data is None:
            return set()
        return {BriefingMilestone(m) for m in data.get("fired", [])}

    def mark_fired(self, calendar_event_id: str, milestone: BriefingMilestone) -> None:
        fired = self.fired_milestones(calendar_event_id)
        fired.add(milestone)
        self._store.put(_ENTITY_TYPE, calendar_event_id, {"fired": [m.value for m in fired]})
