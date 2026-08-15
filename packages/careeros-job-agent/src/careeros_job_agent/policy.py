"""Qualification policy: decides whether a discovered opportunity is worth pursuing.

Deliberately simple and explainable — a match-score threshold — not a
black box. Phase 21 (Autonomous Decision & Authorization) builds a much
richer policy/authorization engine on top of this; this is the first,
honest version of "is this worth pursuing?".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualificationPolicy:
    min_match_score: float = 0.6

    def is_qualified(self, match_score: float | None) -> bool:
        return match_score is not None and match_score >= self.min_match_score
