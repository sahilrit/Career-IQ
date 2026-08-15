"""UnifiedMarketplace: the roadmap's "two marketplace categories" —
Integrations (Phase 48's PluginMarketplace: external services) and AI
Skills (this phase's AISkillMarketplace: intelligence CareerOS's own
packages provide) — as one entry point, each still independently
usable on its own.
"""

from __future__ import annotations

from careeros_plugin_marketplace import PluginMarketplace
from careeros_skill_marketplace.skill_marketplace import AISkillMarketplace


class UnifiedMarketplace:
    def __init__(self, integrations: PluginMarketplace, ai_skills: AISkillMarketplace) -> None:
        self.integrations = integrations
        self.ai_skills = ai_skills

    def search_all(self, query: str) -> dict[str, list]:
        return {
            "integrations": self.integrations.search(query),
            "ai_skills": self.ai_skills.search(query),
        }
