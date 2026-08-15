"""AISkillMarketplace: browse and search the AI Skills section."""

from __future__ import annotations

from careeros_skill_marketplace.exceptions import SkillNotFoundError
from careeros_skill_marketplace.skill_listing import AISkillCategory, AISkillListing


class AISkillMarketplace:
    def __init__(self, skills: list[AISkillListing]) -> None:
        self._skills = list(skills)

    def list_skills(self, *, category: AISkillCategory | None = None) -> list[AISkillListing]:
        if category is None:
            return list(self._skills)
        return [skill for skill in self._skills if skill.category == category]

    def available_skills(self) -> list[AISkillListing]:
        return [skill for skill in self._skills if skill.is_available]

    def search(self, query: str) -> list[AISkillListing]:
        lowered = query.lower()
        return [
            skill
            for skill in self._skills
            if lowered in skill.name.lower() or lowered in skill.description.lower()
        ]

    def get(self, skill_id: str) -> AISkillListing:
        for skill in self._skills:
            if skill.skill_id == skill_id:
                return skill
        raise SkillNotFoundError(f"No AI skill listing for {skill_id!r}")
