"""Achievement matching: rank a user's achievements by relevance to text.

Built on careeros_memory's local, zero-cost TF-IDF index (Phase 5) — this
is the "Memory integration" this phase calls for: Career Brain's raw
achievement records become ranked, targeted evidence for a specific
opportunity instead of a flat list.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_career_brain import Achievement, CareerBrain
from careeros_memory import LocalTfidfIndex


@dataclass
class RankedAchievement:
    achievement: Achievement
    relevance: float


def rank_achievements_for_text(
    brain: CareerBrain, text: str, *, top_k: int = 5
) -> list[RankedAchievement]:
    """Rank every achievement across all experiences by relevance to ``text``."""
    achievements = [
        achievement for experience in brain.experiences for achievement in experience.achievements
    ]
    if not achievements:
        return []

    index = LocalTfidfIndex()
    for achievement in achievements:
        index.index(achievement.id, achievement.description)

    scored = dict(index.search(text, top_k=len(achievements)))
    ranked = [
        RankedAchievement(achievement=achievement, relevance=scored[achievement.id])
        for achievement in achievements
        if achievement.id in scored
    ]
    ranked.sort(key=lambda r: r.relevance, reverse=True)
    return ranked[:top_k]
