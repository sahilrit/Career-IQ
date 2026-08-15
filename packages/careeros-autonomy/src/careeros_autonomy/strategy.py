"""Named autonomy strategies: presets adjusting how cautious the policy is.

Phase 41's CEO Agent later decides resource allocation across divisions
with real market feedback; this is the lighter-weight, present-day
version — a few sane presets rather than a learned allocation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AutonomyStrategy:
    name: str
    min_match_score: float
    min_seconds_between_actions: float


CONSERVATIVE = AutonomyStrategy(
    name="conservative", min_match_score=0.8, min_seconds_between_actions=30.0
)
BALANCED = AutonomyStrategy(name="balanced", min_match_score=0.6, min_seconds_between_actions=10.0)
AGGRESSIVE = AutonomyStrategy(
    name="aggressive", min_match_score=0.4, min_seconds_between_actions=2.0
)
